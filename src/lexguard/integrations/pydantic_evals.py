from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from ..lexicon import Bundle, Lexicon
from ..rulespec import Check, ObserveSpec

SKIP: dict = {}


def _lexicons(target: Lexicon | Bundle) -> list[Lexicon]:
    result = list(target.members) if isinstance(target, Bundle) else [target]
    assert result, "a rule needs at least one lexicon"
    return result


def absent(target: Lexicon | Bundle, **guards: Any) -> Rule:
    """A pydantic-evals evaluator asserting the lexicon (or bundle) is absent from the output."""
    rule = Rule(lexicons=_lexicons(target), wanted=False, **guards)
    assert rule.wanted is False, "absent() builds a not-wanted rule"
    return rule


def expected(target: Lexicon | Bundle, **guards: Any) -> Rule:
    """A pydantic-evals evaluator asserting the lexicon (or bundle) is present in the output."""
    rule = Rule(lexicons=_lexicons(target), wanted=True, **guards)
    assert rule.wanted is True, "expected() builds a wanted rule"
    return rule


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
        check = Check(self.lexicons, self.wanted, self.when, self.unless, self.field, self.of)
        verdicts = check.run(ctx.output, ctx.inputs)
        if verdicts is None:
            return SKIP
        result = {v.name: EvaluationReason(value=v.passed, reason=v.reason) for v in verdicts}
        assert len(result) == len(verdicts), "one reason per verdict; names must be unique"
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
        mapping = result if result is not None else SKIP
        assert mapping is not None, "Observe returns a mapping, empty when the rule abstains"
        return mapping
