from __future__ import annotations

from inspect_ai.scorer import CORRECT, INCORRECT, Score, Scorer, Target, accuracy, scorer
from inspect_ai.solver import TaskState

from ..rulespec import Check


def lexguard_scorer(check: Check) -> Scorer:
    """Build an Inspect AI `Scorer` from a `Check` (from `Lexicon.check()` / `Bundle.check()`).

    Scores `CORRECT` when every lexicon in the check holds, `INCORRECT` otherwise, with the usual
    lexguard diagnosis as the explanation. A check whose guard did not fire, or whose field was
    empty, scores `CORRECT`: silence is not a failure any more than it is a pass elsewhere in
    lexguard.
    """
    assert check.lexicons, "lexguard_scorer needs a Check with at least one lexicon"

    @scorer(metrics=[accuracy()])
    def _lexguard_scorer() -> Scorer:
        async def score(state: TaskState, target: Target) -> Score:
            assert check.lexicons, "the scorer needs a check with at least one lexicon"
            output = state.output.completion
            verdicts = check.run(output, state.input_text)
            if verdicts is None:
                return Score(value=CORRECT, answer=output, explanation="rule did not apply")
            failed = [v for v in verdicts if not v.passed]
            explanation = "\n".join(v.reason for v in failed if v.reason)
            result = Score(
                value=INCORRECT if failed else CORRECT,
                answer=output,
                explanation=explanation or "all lexicon checks passed",
            )
            assert result.value in (CORRECT, INCORRECT), "score is CORRECT or INCORRECT"
            return result

        assert callable(score), "the scorer closure must be callable"
        assert score.__name__ == "score", "Inspect keys the scorer by its function name"
        return score

    result = _lexguard_scorer()
    assert result is not None, "the scorer decorator returns a scorer"
    return result
