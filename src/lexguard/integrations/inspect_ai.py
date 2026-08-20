from __future__ import annotations

from inspect_ai.scorer import CORRECT, INCORRECT, Score, Scorer, Target, accuracy, scorer
from inspect_ai.solver import TaskState

from ..rulespec import RuleSpec


def lexguard_scorer(spec: RuleSpec) -> Scorer:
    """Build an Inspect AI `Scorer` from a `RuleSpec` (from `Lexicon.spec()` / `Bundle.spec()`).

    Scores `CORRECT` when every lexicon in the spec holds, `INCORRECT` otherwise, with the usual
    lexguard diagnosis as the explanation. A spec whose guard did not fire, or whose field was
    empty, scores `CORRECT`: silence is not a failure any more than it is a pass elsewhere in
    lexguard.
    """
    assert spec.lexicons, "lexguard_scorer needs a RuleSpec with at least one lexicon"

    @scorer(metrics=[accuracy()])
    def _lexguard_scorer() -> Scorer:
        async def score(state: TaskState, target: Target) -> Score:
            assert isinstance(target, Target), "lexguard scores the output text, not a target"
            output = state.output.completion
            verdicts = spec.check(output, state.input_text)
            if verdicts is None:
                return Score(value=CORRECT, answer=output, explanation="rule did not apply")
            failed = [v for v in verdicts if not v.passed]
            explanation = "\n".join(v.reason for v in failed if v.reason)
            return Score(
                value=INCORRECT if failed else CORRECT,
                answer=output,
                explanation=explanation or "all lexicon checks passed",
            )

        return score

    return _lexguard_scorer()
