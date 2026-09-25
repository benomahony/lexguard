from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from typing import Literal

from pydantic_ai.exceptions import ModelRetry
from pydantic_ai.toolsets import FunctionToolset
from pydantic_ai_harness.guardrails import GuardrailResult, OutputGuardrail, OutputGuardrailFunc

from lexguard.lexicon import Bundle, Lexicon, tidy


def lexguard_guard(
    target: Lexicon | Bundle,
    *,
    on_fail: Literal["block", "retry"] = "retry",
) -> Callable[[object], GuardrailResult]:
    """Build a pydantic-ai-harness guard from a `Lexicon` (or a `Bundle` of them), checked
    against the value it's given. Whether each lexicon asserts presence or absence is its own
    `fail_when_neutral`; see `Lexicon.verdict`.

    A guard returns exactly one result — unlike the eval-framework adapters, a `Bundle`
    here does combine into a single decision, since that's the only shape a guard can return.
    Failing on more than one lexicon still lists every one that failed, so nothing is hidden;
    only the guardrail action itself is combined.

    By default a failed verdict retries, giving the model the lexicon failure reason and
    another attempt. Set `on_fail="block"` for input guardrails, or anywhere a retry isn't
    appropriate and the value should be rejected outright.

    The same callable shape works for `InputGuardrail`, `OutputGuardrail`, and the argument half
    of `ToolGuardrail` — pick whichever the check belongs to:

        OutputGuardrail(guard=lexguard_guard(Slop))
        InputGuardrail(guard=lexguard_guard(Confidential, on_fail="block"))
    """
    lexicons = target.members if isinstance(target, Bundle) else (target,)
    assert lexicons, "a guard needs at least one lexicon to check"
    assert all(lexicon.name for lexicon in lexicons), "every lexicon has a name"

    def guard(value: object) -> GuardrailResult:
        text = str(value)
        verdicts = [lexicon.verdict(text) for lexicon in lexicons]
        assert len(verdicts) == len(lexicons), "one verdict per lexicon checked"

        failures = [verdict for verdict in verdicts if not verdict.passed]
        if not failures:
            return GuardrailResult.allow()

        reason = "\n\n".join(failure.reason or "" for failure in failures)
        result = (
            GuardrailResult.retry(reason) if on_fail == "retry" else GuardrailResult.block(reason)
        )
        assert result is not None, "a guard always returns a result"
        return result

    assert callable(guard), "the guard closure must be callable"
    return guard


GUIDANCE = (
    "Your output is checked against lexguards: named word lists that fail a reply on a match. "
    "Call `list_lexguards` to see them, `update_lexguard` to add or remove terms or create a new "
    "one (e.g. when the user bans a word), and `remove_lexguard` to drop one. Changes apply to "
    "your very next output."
)


@dataclass
class DynamicLexguard(OutputGuardrail[object]):
    """An `OutputGuardrail` over a set of lexicons the agent itself can edit mid-run.

    Unlike pydantic-ai-harness `CapabilityCreation`, which authors code that only goes live on the
    next run, lexicons are data: an edit made through the tools is checked against the very next
    output of the same run. The edited set lives on the capability, so it carries across runs of
    the same agent, and `lexicons` shows what the agent has changed.

        agent = Agent(model, capabilities=[DynamicLexguard(Slop | Padding)])
    """

    target: Lexicon | Bundle | None = None
    on_fail: Literal["block", "retry"] = "retry"
    guidance: str = GUIDANCE
    guard: OutputGuardrailFunc[object] | Sequence[OutputGuardrailFunc[object]] = field(init=False)
    lexicons: dict[str, Lexicon] = field(init=False)

    def __post_init__(self) -> None:
        target = self.target
        members = target.members if isinstance(target, Bundle) else (target,) if target else ()
        self.lexicons = {lexicon.name: lexicon for lexicon in members}
        self.guard = self.check
        assert set(self.lexicons) == {lexicon.name for lexicon in members}, "one per name"

    def check(self, value: object) -> GuardrailResult:
        if not self.lexicons:
            return GuardrailResult.allow()
        bundle = Bundle(members=tuple(self.lexicons.values()))
        return lexguard_guard(bundle, on_fail=self.on_fail)(value)

    def get_instructions(self) -> str | None:
        return self.guidance or None

    def get_toolset(self) -> FunctionToolset[object]:
        toolset = FunctionToolset[object]()
        toolset.add_function(self.list_lexguards, name="list_lexguards")
        toolset.add_function(self.update_lexguard, name="update_lexguard")
        toolset.add_function(self.remove_lexguard, name="remove_lexguard")
        return toolset

    def list_lexguards(self) -> str:
        """List every active lexguard as a paste-able `Lexicon(...)` expression."""
        if not self.lexicons:
            return "No lexguards are active."
        return "\n".join(lexicon.as_code() for lexicon in self.lexicons.values())

    def update_lexguard(
        self,
        name: str,
        indicates: list[str] | None = None,
        rules_out: list[str] | None = None,
        remove: list[str] | None = None,
        fix: str | None = None,
        fail_when_neutral: bool | None = None,
    ) -> str:
        """Create a lexguard, or edit an existing one in place.

        Args:
            name: The lexguard to edit or create, lowercase with underscores (e.g. `slop`).
            indicates: Terms to add that fail the output when they appear.
            rules_out: Terms to add that cancel an `indicates` match (e.g. a negation).
            remove: Terms to drop from both lists.
            fix: One sentence telling the writer what to do on a match. Required to create.
            fail_when_neutral: True to fail when no term appears, rather than when one does.
        """
        added, blockers, dropped = tidy(indicates or ()), tidy(rules_out or ()), tidy(remove or ())
        if added & blockers:
            raise ModelRetry(f"a term can't both indicate and rule out: {sorted(added & blockers)}")
        existing = self.lexicons.get(name)
        if existing is None and not fix:
            raise ModelRetry(f"no lexguard named {name!r} yet; pass a `fix` to create it")
        base = existing or Lexicon(name=name, indicates=(), fix=fix or "")
        lexicon = replace(
            base,
            indicates=(frozenset(base.indicates) - blockers - dropped) | added,
            rules_out=(frozenset(base.rules_out) - added - dropped) | blockers,
            fix=fix or base.fix,
            fail_when_neutral=(
                base.fail_when_neutral if fail_when_neutral is None else fail_when_neutral
            ),
        )
        self.lexicons[name] = lexicon
        assert self.lexicons[name] is lexicon, "the edit is live for the next check"
        return f"{'updated' if existing else 'created'} {lexicon!r}"

    def remove_lexguard(self, name: str) -> str:
        """Stop checking output against a lexguard.

        Args:
            name: The lexguard to remove.
        """
        if self.lexicons.pop(name, None) is None:
            return f"No lexguard named {name!r}."
        return f"removed {name}"
