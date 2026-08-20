"""A self-improving agent that authors its own lexicon *as code*.

This mirrors the runtime capability-creation pattern from
[pydantic-ai-harness](https://github.com/pydantic/pydantic-ai-harness): the agent
writes a capability to disk as Python source, validates it, and the orchestrator
loads it into the *next* `agent.run(...)`. Here the capability is a lexguard
`Lexicon` — the guard on the agent's own prose — and lexicons are already just
code (three lists and a sentence), so the authored artifact is an ordinary
module you could commit:

    from lexguard import Slop

    GUARD = Slop.extend(
        indicates=["circle back", "move the needle"],
        rules_out=["test harness"],
    )

The agent holds a workspace (a path plus what it has learned) as a dependency,
and two tools edit the guard: `flag_slop` adds filler the guard let through,
`excuse` adds an innocent phrase it wrongly fired on. Each tool call rewrites the
source file and reloads it, so the guard is always exactly what is on disk. Every
`agent.run(...)` reloads the guard from that file first, which is what makes the
loop self-improving across runs rather than only within one.

Driven by `FunctionModel` so it runs deterministically without an API key — the
same way `TestModel` stands in for a live model elsewhere in these examples. The
`Agent`, the tools, the run loop, the generated source, and the reload are all
real; only the model's choices are scripted, and even those are gated on what the
live guard does not yet know.
"""

from __future__ import annotations

import importlib.util
import tempfile
from dataclasses import dataclass, field
from itertools import count
from pathlib import Path

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    TextPart,
    ToolCallPart,
    UserPromptPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

from lexguard import Lexicon


def render_source(indicates: list[str], rules_out: list[str]) -> str:
    """Turn what the agent has learned into an importable lexicon module."""
    header = '"""Guard authored by the agent from reviewer feedback."""'
    lines = [header, "", "from lexguard import Slop", ""]
    if not indicates and not rules_out:
        lines.append("GUARD = Slop")
    else:
        lines.append("GUARD = Slop.extend(")
        for name, learned in (("indicates", indicates), ("rules_out", rules_out)):
            if learned:
                lines.append(f"    {name}=[")
                lines += [f"        {phrase!r}," for phrase in sorted(set(learned))]
                lines.append("    ],")
        lines.append(")")
    return "\n".join([*lines, ""])


def load_guard(path: Path) -> Lexicon:
    """Load (and thereby validate) the authored guard, the way the next run would."""
    name = f"authored_guard_{next(_loads)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot import authored guard at {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # runs the source; a broken edit would raise here
    guard = module.GUARD
    assert isinstance(guard, Lexicon), "authored module must define a GUARD lexicon"
    return guard


_loads = count()


@dataclass
class Workspace:
    """The agent's evolving capability, persisted as a Python source file on disk."""

    path: Path
    indicates: list[str] = field(default_factory=list)
    rules_out: list[str] = field(default_factory=list)

    def author(self) -> Lexicon:
        """Write the guard to disk as code, then load it back."""
        self.path.write_text(render_source(self.indicates, self.rules_out))
        return load_guard(self.path)


agent = Agent(
    deps_type=Workspace,
    system_prompt=(
        "You gate your own prose for slop. Score the draft against your guard, and when a "
        "reviewer flags filler your guard missed, flag_slop it so you catch it next time."
    ),
)


@agent.tool
def flag_slop(ctx: RunContext[Workspace], phrase: str) -> str:
    """Teach the guard a filler phrase it let through, and persist it as code."""
    ctx.deps.indicates.append(phrase)
    guard = ctx.deps.author()
    assert guard.fires(phrase), "a flagged phrase must fire once it is written to the guard"
    return f"wrote {phrase!r} to {ctx.deps.path.name}; guard now knows {len(guard.indicates)}"


@agent.tool
def excuse(ctx: RunContext[Workspace], phrase: str) -> str:
    """Teach the guard that a phrase is innocent, retiring a false alarm."""
    ctx.deps.rules_out.append(phrase)
    guard = ctx.deps.author()
    assert guard.denied(phrase), "an excused phrase must be denied once it is written to the guard"
    return f"wrote rules_out {phrase!r} to {ctx.deps.path.name}; guard now overrides on it"


# What a competent writer recognizes as filler once it is pointed out. The scripted
# model only ever flags a candidate the *live, on-disk* guard does not already catch,
# so the second run has less to learn than the first — the loop is converging.
KNOWN_SLOP = ["circle back", "move the needle", "north star", "boil the ocean"]
KNOWN_INNOCENT = ["test harness"]


def last_user_text(messages: list[ModelMessage]) -> str:
    for message in reversed(messages):
        for part in message.parts:
            if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                return part.content
    return ""


def reviewer(workspace: Workspace):
    """A FunctionModel that reasons over the draft against the guard on disk right now."""

    def model_fn(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        # reload every turn so the model sees the edits its own tool calls just wrote
        guard = load_guard(workspace.path)
        draft = last_user_text(messages).casefold()
        for phrase in KNOWN_SLOP:
            if phrase in draft and not guard.fires(phrase):
                return ModelResponse(parts=[ToolCallPart("flag_slop", {"phrase": phrase})])
        for phrase in KNOWN_INNOCENT:
            if phrase in draft and guard.fires(phrase):
                return ModelResponse(parts=[ToolCallPart("excuse", {"phrase": phrase})])
        verdict = guard.signal(draft).name
        present = sorted(guard.hits(draft)) or "none"
        return ModelResponse(parts=[TextPart(f"{verdict}; indicators present: {present}")])

    return model_fn


def gate(workspace: Workspace, draft: str) -> str:
    """One agent.run over a draft; the reviewer reads the authored guard from disk each turn."""
    result = agent.run_sync(
        f"Gate this draft, flagging any filler your guard misses:\n\n{draft}",
        model=FunctionModel(reviewer(workspace)),
        deps=workspace,
    )
    assert result.output
    return result.output


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Workspace(path=Path(tmp) / "guard.py")
        started_with = len(workspace.author().indicates)  # the shipped Slop, written as code

        drafts = [
            "We should circle back, boil the ocean on the north star, and move the needle.",
            "The retry path used to swallow errors; now it surfaces them to the caller.",
            "The test harness passed on the first try after the retry fix landed.",
        ]
        for i, draft in enumerate(drafts):
            print(f"run {i}: guard on disk knows {len(load_guard(workspace.path).indicates)}")
            print(f"  draft:   {draft}")
            print(f"  verdict: {gate(workspace, draft)}")
            print()

        print("the agent's authored guard.py now reads:\n")
        print("    " + workspace.path.read_text().replace("\n", "\n    ").rstrip())
        print()

        # The point of the loop: a brand-new process (here, a fresh load) picks up
        # everything the agent wrote. "circle back" sailed through the shipped Slop;
        # the authored guard catches it, and "test harness" it excused stays quiet.
        trained = load_guard(workspace.path)
        assert len(trained.indicates) > started_with
        assert trained.fires("let us circle back on this")
        assert trained.denied("we finally have a green test harness")
        print("reloaded from code: catches 'circle back' and excuses 'test harness'")


if __name__ == "__main__":
    main()
