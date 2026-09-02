from __future__ import annotations

from collections.abc import Callable

from pydantic_ai_harness.guardrails import GuardrailResult

from lexguard.lexicon import Bundle, Lexicon


def lexguard_guard(target: Lexicon | Bundle) -> Callable[[object], GuardrailResult]:
    """Build a pydantic-ai-harness guard from a `Lexicon` (or a `Bundle` of them), checked
    against the value it's given. Whether each lexicon asserts presence or absence is its own
    `fail_when_neutral`; see `Lexicon.verdict`.

    A guard returns exactly one `allow`/`block` — unlike the eval-framework adapters, a `Bundle`
    here does combine into a single decision, since that's the only shape a guard can return.
    Blocking on more than one lexicon still lists every one that failed, so nothing is hidden;
    only the pass/fail action itself is combined.

    The same callable shape works for `InputGuardrail`, `OutputGuardrail`, and the argument half
    of `ToolGuardrail` — pick whichever the check belongs to:

        OutputGuardrail(guard=lexguard_guard(Slop))
        InputGuardrail(guard=lexguard_guard(Confidential))
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
        result = GuardrailResult.block("\n\n".join(failure.reason or "" for failure in failures))
        assert result is not None, "a guard always returns a result"
        return result

    assert callable(guard), "the guard closure must be callable"
    return guard
