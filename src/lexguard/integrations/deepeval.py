from __future__ import annotations

from typing import Any

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

from ..rulespec import RuleSpec


class LexguardMetric(BaseMetric):
    """Wrap a `RuleSpec` (from `Lexicon.spec()` / `Bundle.spec()`) as a DeepEval metric.

    `score` is the fraction of lexicons in the spec that passed; the default `threshold=1.0`
    means every lexicon must hold, mirroring `.absent()` / `.expected()` semantics. A spec whose
    guard did not fire, or whose field was empty, scores 1.0 rather than failing the test case:
    silence is not a failure any more than it is a pass elsewhere in lexguard.
    """

    def __init__(self, spec: RuleSpec, threshold: float = 1.0) -> None:
        assert spec.lexicons, "LexguardMetric needs a RuleSpec with at least one lexicon"
        assert 0.0 <= threshold <= 1.0, "threshold is a pass-fraction, must be between 0 and 1"
        self.spec = spec
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
        assert self.spec.lexicons, "LexguardMetric needs at least one lexicon to name itself"
        stem = "has" if self.spec.wanted else "no"
        result = f"{stem}_{'_'.join(lexicon.name for lexicon in self.spec.lexicons)}"
        assert result.startswith(stem), "metric name is prefixed by has/no"
        return result

    def measure(self, test_case: LLMTestCase, *args: Any, **kwargs: Any) -> float:
        verdicts = self.spec.check(test_case.actual_output, test_case.input)
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
        assert isinstance(test_case, LLMTestCase), "a_measure takes an LLMTestCase"
        result = self.measure(test_case, *args, **kwargs)
        assert isinstance(result, float), "measure() returns a float score"
        return result
