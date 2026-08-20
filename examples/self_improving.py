"""A self-improving agent that authors its own lexicon at runtime.

This mirrors the capability-creation pattern from
[pydantic-ai-harness](https://github.com/pydantic/pydantic-ai-harness): an agent
discovers mid-run that its guard is missing something, writes the fix, and the
improved guard is loaded into the *next* run. Here the capability the agent
extends is a lexguard `Lexicon` — the guard on its own prose.

The agent holds its current lexicon as a dependency and is given two tools that
edit it: `flag_slop` folds filler the guard let through into `indicates`, and
`excuse` folds an innocent phrase the guard wrongly fired on into `rules_out`.
Every edit persists on the dependency, so the lexicon carried into the next
`agent.run(...)` is the one the last run taught.

Driven by `FunctionModel` so it runs deterministically without an API key — the
same way `TestModel` stands in for a live model elsewhere in these examples. The
`Agent`, the tools, the run loop, and the growing lexicon are all real; only the
model's choices are scripted, and even those are gated on what the live guard
does not yet know.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    TextPart,
    ToolCallPart,
    UserPromptPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

from lexguard import Lexicon, Slop


@dataclass
class Guard:
    """The agent's evolving capability: the lexicon it uses to gate its writing."""

    lexicon: Lexicon


agent = Agent(
    deps_type=Guard,
    system_prompt=(
        "You gate your own prose for slop. Score the draft against your guard, and when a "
        "reviewer flags filler your guard missed, flag_slop it so you catch it next time."
    ),
)


@agent.tool
def flag_slop(ctx: RunContext[Guard], phrase: str) -> str:
    """Teach the guard a filler phrase it let through."""
    before = len(ctx.deps.lexicon.indicates)
    ctx.deps.lexicon = ctx.deps.lexicon.extend(indicates=[phrase])
    grew = len(ctx.deps.lexicon.indicates) - before
    assert ctx.deps.lexicon.fires(phrase), "a flagged phrase must fire afterwards"
    return f"learned {phrase!r} (+{grew}); guard now knows {len(ctx.deps.lexicon.indicates)}"


@agent.tool
def excuse(ctx: RunContext[Guard], phrase: str) -> str:
    """Teach the guard that a phrase is innocent, retiring a false alarm."""
    ctx.deps.lexicon = ctx.deps.lexicon.extend(rules_out=[phrase])
    assert ctx.deps.lexicon.denied(phrase), "an excused phrase must be denied afterwards"
    return f"excused {phrase!r}; guard now overrides on it"


# What a competent writer recognizes as filler once it is pointed out. The scripted
# model only ever flags a candidate the *live* guard does not already catch, so the
# second run has less to learn than the first — the loop is converging.
KNOWN_SLOP = ["circle back", "move the needle", "north star", "boil the ocean"]
KNOWN_INNOCENT = ["test harness"]


def last_user_text(messages: list[ModelMessage]) -> str:
    for message in reversed(messages):
        for part in message.parts:
            if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                return part.content
    return ""


def reviewer(guard: Guard):
    """A FunctionModel that reasons over the draft against the guard's live vocabulary."""

    def model_fn(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        draft = last_user_text(messages).casefold()
        # Flag filler that is in the draft but that the guard does not yet catch.
        for phrase in KNOWN_SLOP:
            if phrase in draft and not guard.lexicon.fires(phrase):
                return ModelResponse(parts=[ToolCallPart("flag_slop", {"phrase": phrase})])
        # Excuse an innocent phrase the guard is wrongly firing on.
        for phrase in KNOWN_INNOCENT:
            if phrase in draft and guard.lexicon.fires(phrase):
                return ModelResponse(parts=[ToolCallPart("excuse", {"phrase": phrase})])
        verdict = guard.lexicon.signal(draft).name
        present = sorted(guard.lexicon.hits(draft)) or "none"
        return ModelResponse(parts=[TextPart(f"{verdict}; indicators present: {present}")])

    return model_fn


def gate(guard: Guard, draft: str) -> str:
    """One agent.run over a draft, letting the agent edit its own guard as it goes."""
    result = agent.run_sync(
        f"Gate this draft, flagging any filler your guard misses:\n\n{draft}",
        model=FunctionModel(reviewer(guard)),
        deps=guard,
    )
    assert result.output
    return result.output


def main() -> None:
    guard = Guard(lexicon=Slop)  # start from exactly what ships in the box
    started_with = len(guard.lexicon.indicates)

    drafts = [
        "We should circle back, boil the ocean on the north star, and move the needle.",
        "The retry path used to swallow errors; now it surfaces them to the caller.",
        "The test harness passed on the first try after the retry fix landed.",
    ]

    for i, draft in enumerate(drafts):
        print(f"run {i}: guard knows {len(guard.lexicon.indicates)} indicators")
        print(f"  draft:   {draft}")
        print(f"  verdict: {gate(guard, draft)}")
        print()

    print(f"the agent grew its guard from {started_with} to {len(guard.lexicon.indicates)}\n")
    assert len(guard.lexicon.indicates) > started_with

    # The point of the loop: what the guard learned on run 0 is loaded into every run
    # after it. "circle back" sailed through the shipped Slop; the agent's own guard now
    # catches it, while "test harness" it excused stays quiet.
    trained = guard.lexicon
    assert trained.fires("let us circle back on this")
    assert not Slop.fires("let us circle back on this"), "the shipped guard never knew this"
    assert trained.denied("we finally have a green test harness")
    print("trained guard catches 'circle back' (Slop never did) and excuses 'test harness'")


if __name__ == "__main__":
    main()
