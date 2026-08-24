from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from .lexicon import Lexicon
from .rulespec import ObserveSpec, RuleSpec

SKIP: dict = {}


@dataclass
class Rule(Evaluator):
    lexicons: Sequence[Lexicon]
    wanted: bool = False
    when: Lexicon | None = None
    unless: Lexicon | None = None
    field: str = ""
    of: Literal["output", "inputs"] = "output"

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, EvaluationReason]:
        assert self.lexicons, "Rule needs at least one lexicon"
        spec = RuleSpec(self.lexicons, self.wanted, self.when, self.unless, self.field, self.of)
        verdicts = spec.check(ctx.output, ctx.inputs)
        if verdicts is None:
            return SKIP
        result = {v.name: EvaluationReason(value=v.passed, reason=v.reason) for v in verdicts}
        assert len(result) == len(verdicts)
        return result


@dataclass
class Observe(Evaluator):
    lexicons: Sequence[Lexicon]
    field: str = ""
    of: Literal["output", "inputs"] = "output"

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, str]:
        assert self.lexicons, "Observe needs at least one lexicon"
        spec = ObserveSpec(self.lexicons, self.field, self.of)
        result = spec.signals(ctx.output, ctx.inputs)
        assert result is None or isinstance(result, dict)
        return result if result is not None else SKIP
