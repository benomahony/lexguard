from __future__ import annotations

from typing import Any

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

from ..rulespec import Check


class LexguardMetric(BaseMetric):
    """Wrap a `Check` (built with `Check([lexicon, ...], ...)`) as a DeepEval metric.

    `score` is the fraction of lexicons in the check that passed; the default `threshold=1.0`
    means every lexicon must hold, the same all-or-nothing semantics a bundle gives. A check whose
    guard did not fire, or whose field was empty, scores 1.0 rather than failing the test case:
    silence is not a failure any more than it is a pass elsewhere in lexguard.
    """

    def __init__(self, check: Check, threshold: float = 1.0) -> None:
        assert check.lexicons, "LexguardMetric needs a Check with at least one lexicon"
        assert 0.0 <= threshold <= 1.0, "threshold is a pass-fraction, must be between 0 and 1"
        self.check = check
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
        assert self.check.lexicons, "LexguardMetric needs at least one lexicon to name itself"
        stem = "has" if self.check.wanted else "no"
        result = f"{stem}_{'_'.join(lexicon.name for lexicon in self.check.lexicons)}"
        assert result.startswith(stem), "metric name is prefixed by has/no"
        return result

    def measure(self, test_case: LLMTestCase, *args: Any, **kwargs: Any) -> float:
        verdicts = self.check.run(test_case.actual_output, test_case.input)
        if verdicts is None:
            self.score, self.reason = 1.0, None
        else:
            self.score = sum(v.passed for v in verdicts) / len(verdicts)
            self.reason = "; ".join(v.reason for v in verdicts if v.reason) or None
        self.success = self.is_successful()
        assert self.score is not None, "measure() always sets a score"
        assert self.success is not None, "measure() always sets success"
        return self.score

    async def a_measure(self, test_case: LLMTestCase, *args: Any, **kwargs: Any) -> float:
        assert self.check.lexicons, "a_measure needs a check with at least one lexicon"
        result = self.measure(test_case, *args, **kwargs)
        assert 0.0 <= result <= 1.0, "the score is a pass-fraction in [0, 1]"
        return result
