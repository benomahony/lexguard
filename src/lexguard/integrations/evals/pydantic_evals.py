from __future__ import annotations

from dataclasses import dataclass

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from lexguard.lexicon import Bundle, Lexicon

__all__ = ["LexguardEvaluator", "Observe"]


def _lexicons(target: Lexicon | Bundle) -> tuple[Lexicon, ...]:
    result = target.members if isinstance(target, Bundle) else (target,)
    assert result, "a Bundle always has at least one member"
    assert all(lexicon.name for lexicon in result), "every member has a name"
    return result


@dataclass
class LexguardEvaluator(Evaluator):
    """Wraps a `Lexicon` (or a `Bundle` of them) as a pydantic-evals `Evaluator` — one assertion
    per lexicon, never merged into a single pass/fail. Whether each lexicon asserts presence or
    absence is its own `fail_when_neutral`, not a flag here; see `Lexicon.verdict`.
    """

    lexicon: Lexicon | Bundle

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, EvaluationReason | str | float]:
        output = str(ctx.output)
        lexicons = _lexicons(self.lexicon)
        result: dict[str, EvaluationReason | str | float] = {}
        for lexicon in lexicons:
            verdict = lexicon.verdict(output)
            result[lexicon.label] = EvaluationReason(value=verdict.passed, reason=verdict.reason)
            density = lexicon.density(output)
            result[f"{lexicon.label}IndicatedDensity"] = density.indicated
            if lexicon.rules_out:
                result[f"{lexicon.label}RuledOutDensity"] = density.ruled_out
            hits = lexicon.hits(output)
            if hits.indicated:
                result[f"{lexicon.label}Indicated"] = ", ".join(sorted(hits.indicated))
            if hits.ruled_out:
                result[f"{lexicon.label}RuledOut"] = ", ".join(sorted(hits.ruled_out))
        assert len(result) >= len(lexicons), "at least one assertion per lexicon"
        assert all(lexicon.label in result for lexicon in lexicons), "every label is a result key"
        return result


@dataclass
class Observe(Evaluator):
    """Label the output with each lexicon's raw signal (present/denied/absent) — not an
    assertion. Accepts a `Lexicon` or a `Bundle`, one label per member.
    """

    lexicon: Lexicon | Bundle

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, str]:
        output = str(ctx.output)
        lexicons = _lexicons(self.lexicon)
        result = {lexicon.label: lexicon.signal(output).value for lexicon in lexicons}
        assert len(result) == len(lexicons), "one label per lexicon, none merged"
        assert all(lexicon.label in result for lexicon in lexicons), "every label is a result key"
        return result
