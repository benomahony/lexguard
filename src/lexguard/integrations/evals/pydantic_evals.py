from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from lexguard import __version__
from lexguard.lexicon import Bundle, Lexicon

__all__ = ["LexguardEvaluator", "Observe"]


def _lexicons(target: Lexicon | Bundle) -> tuple[Lexicon, ...]:
    result = target.members if isinstance(target, Bundle) else (target,)
    assert result, "a Bundle always has at least one member"
    assert all(lexicon.name for lexicon in result), "every member has a name"
    return result


def _oriented_density(lexicon: Lexicon, output: str) -> tuple[str, float]:
    # the lexicon's own fail_when_neutral says which way is good, so the score reads higher=better
    indicated = lexicon.density(output).indicated
    result = (
        (f"{lexicon.label}Density", indicated)
        if lexicon.fail_when_neutral
        else (f"Not{lexicon.label}Density", 1.0 - indicated)
    )
    assert result[0].endswith(f"{lexicon.label}Density"), "the score is named for its lexicon"
    assert 0.0 <= result[1] <= 1.0, "an oriented density stays a fraction"
    return result


class _Identified:
    """Mixed into every evaluator here: how it identifies itself to pydantic-evals, which copies
    that into each result it emits (e.g. `gen_ai.evaluation.evaluator.source` over OTel). A plain
    mixin, not an `Evaluator` subclass, because pydantic-evals rejects a subclass that leaves
    `evaluate` unimplemented.
    """

    lexicon: Lexicon | Bundle

    def build_serialization_arguments(self) -> dict[str, Any]:
        # the default dumps every member's full word lists and fix text, ~10 KB per emitted event;
        # the labels are enough to identify which lexicons ran, and the version pins which words
        labels = [lexicon.label for lexicon in _lexicons(self.lexicon)]
        result: dict[str, Any] = {
            "lexicon": labels if isinstance(self.lexicon, Bundle) else labels[0]
        }
        assert labels, "at least one lexicon is identified"
        assert len(result) == 1, "only the labels, never the word lists"
        return result

    def get_evaluator_version(self) -> str:
        # word lists change between releases, so dashboards need to tell old scores from new
        assert __version__, "lexguard always has a version"
        assert __version__.count(".") == 2, "a release version, as bump-my-version writes it"
        return __version__


@dataclass
class LexguardEvaluator(_Identified, Evaluator):
    """Wraps a `Lexicon` (or a `Bundle` of them) as a pydantic-evals `Evaluator` — one assertion
    per lexicon, never merged into a single pass/fail. Whether each lexicon asserts presence or
    absence is its own `fail_when_neutral`, not a flag here; see `Lexicon.verdict`.

    Set `density=True` to add one density score per lexicon, oriented so higher always reads as
    better: `{Label}Density` for a lexicon you want present, `Not{Label}Density` (one minus the
    hit density) for one you want absent. Off by default: backends render every score as a
    quality percentage, and a raw "0% slop" reads as a failure next to the pass rates.
    """

    lexicon: Lexicon | Bundle
    density: bool = False

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, EvaluationReason | str | float]:
        output = str(ctx.output)
        lexicons = _lexicons(self.lexicon)
        result: dict[str, EvaluationReason | str | float] = {}
        for lexicon in lexicons:
            verdict = lexicon.verdict(output)
            result[lexicon.label] = EvaluationReason(value=verdict.passed, reason=verdict.reason)
            if self.density:
                key, score = _oriented_density(lexicon, output)
                result[key] = score
            hits = lexicon.hits(output)
            if hits.indicated:
                result[f"{lexicon.label}Indicated"] = ", ".join(sorted(hits.indicated))
            if hits.ruled_out:
                result[f"{lexicon.label}RuledOut"] = ", ".join(sorted(hits.ruled_out))
        assert len(result) >= len(lexicons), "at least one assertion per lexicon"
        assert all(lexicon.label in result for lexicon in lexicons), "every label is a result key"
        return result

    def build_serialization_arguments(self) -> dict[str, Any]:
        result = super().build_serialization_arguments()
        if self.density:
            result["density"] = True
        assert "lexicon" in result, "the lexicons that ran are always identified"
        assert len(result) <= 2, "only labels and the density flag, never the word lists"
        return result


@dataclass
class Observe(_Identified, Evaluator):
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
