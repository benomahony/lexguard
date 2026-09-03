from __future__ import annotations

from typing import Any

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

from lexguard.lexicon import Lexicon


class LexguardMetric(BaseMetric):
    """Wrap a single `Lexicon` as a DeepEval metric, checked against `actual_output`. Whether it
    asserts presence or absence is the lexicon's own `fail_when_neutral`; see `Lexicon.verdict`.

    Score is 1.0 on a pass, 0.0 on a fail — one lexicon per metric, so a failing score always
    points at exactly what failed rather than an averaged fraction.
    """

    def __init__(self, lexicon: Lexicon, threshold: float = 1.0) -> None:
        assert 0.0 <= threshold <= 1.0, "threshold is a pass-fraction, must be between 0 and 1"
        assert lexicon.name, "a metric needs a real lexicon to check"
        self.lexicon = lexicon
        self.threshold = threshold
        self.async_mode = False
        self.strict_mode = False
        self.include_reason = True
        self.score: float | None = None
        self.success: bool | None = None
        self.reason: str | None = None
        self.error: str | None = None

    @property
    def __name__(self) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
        result = self.lexicon.label
        assert result, "a metric always has a name"
        assert result == self.lexicon.label, "the metric name is stable across calls"
        return result

    def measure(self, test_case: LLMTestCase, *args: Any, **kwargs: Any) -> float:
        output = str(test_case.actual_output)
        verdict = self.lexicon.verdict(output)
        density = self.lexicon.density(output)
        self.score = 1.0 if verdict.passed else 0.0
        self.reason = verdict.reason
        self.score_breakdown = {"indicated": density.indicated}
        if self.lexicon.rules_out:
            self.score_breakdown["ruled_out"] = density.ruled_out
        self.success = self.is_successful()
        assert self.score is not None, "measure() always sets a score"
        assert self.success is not None, "measure() always sets success"
        return self.score

    async def a_measure(self, test_case: LLMTestCase, *args: Any, **kwargs: Any) -> float:
        result = self.measure(test_case, *args, **kwargs)
        assert 0.0 <= result <= 1.0, "the score is a pass-fraction in [0, 1]"
        assert result == self.score, "a_measure returns exactly what measure set"
        return result
