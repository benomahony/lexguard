from __future__ import annotations

from inspect_ai.scorer import CORRECT, INCORRECT, Score, Scorer, Target, accuracy, scorer
from inspect_ai.solver import TaskState

from lexguard.lexicon import Lexicon


def lexguard_scorer(lexicon: Lexicon) -> Scorer:
    """Build an Inspect AI `Scorer` from a single `Lexicon`, checked against the completion.
    Whether it asserts presence or absence is the lexicon's own `fail_when_neutral`; see
    `Lexicon.verdict`. Scores `CORRECT` on a pass, `INCORRECT` otherwise, with the usual lexguard
    diagnosis as the explanation.
    """
    assert lexicon.name, "a scorer needs a real lexicon to check"

    @scorer(metrics=[accuracy()])
    def _lexguard_scorer() -> Scorer:
        async def score(state: TaskState, target: Target) -> Score:
            assert target is not None, "Inspect always passes a target, even when unused here"
            output = state.output.completion
            verdict = lexicon.verdict(output)
            result = Score(
                value=CORRECT if verdict.passed else INCORRECT,
                answer=output,
                explanation=verdict.reason or "the lexicon check passed",
            )
            assert result.value in (CORRECT, INCORRECT), "score is CORRECT or INCORRECT"
            assert result.answer == output, "the score reports the completion it judged"
            return result

        assert callable(score), "the scorer closure must be callable"
        assert score.__name__ == "score", "Inspect keys the scorer by its function name"
        return score

    result = _lexguard_scorer()
    assert result is not None, "the scorer decorator returns a scorer"
    assert callable(result), "a Scorer is always callable"
    return result
