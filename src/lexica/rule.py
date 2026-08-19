from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from .lexicon import Lexicon, snippet

SKIP: dict[str, Any] = {}


def _attr(obj: Any, key: str) -> Any:
    assert obj is not None, "cannot look up an attribute on a missing value"
    assert key, "path segment must not be empty"
    if isinstance(obj, Mapping):
        return obj.get(key)
    try:
        return vars(obj).get(key)
    except TypeError:
        return None


def read(obj: Any, path: str) -> list[Any]:
    assert not path or all(segment for segment in path.split(".")), (
        "path must not contain empty segments"
    )
    values = [obj] if obj is not None else []
    for head in path.split(".") if path else []:
        many = head.endswith("[]")
        key = head[:-2] if many else head
        step: list[Any] = []
        for value in values:
            attr = _attr(value, key)
            if attr is None:
                continue
            step.extend(attr) if many else step.append(attr)
        values = step
    assert all(value is not None for value in values)
    return values


def text_at(obj: Any, path: str) -> str:
    if not path:
        return str(obj)
    values = read(obj, path)
    result = " ".join(str(value) for value in values)
    assert bool(result) == bool(values)
    assert "\n" not in result or any("\n" in str(value) for value in values)
    return result


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
        assert not (self.when and self.unless), "a Rule cannot have both when and unless"
        request = str(ctx.inputs)
        if self.when is not None and not self.when.fires(request):
            return SKIP
        if self.unless is not None and self.unless.fires(request):
            return SKIP
        body = text_at(ctx.output if self.of == "output" else ctx.inputs, self.field)
        if not body.strip():
            return SKIP
        return {self._name(entry): self._verdict(entry, body, request) for entry in self.lexicons}

    def _name(self, lexicon: Lexicon) -> str:
        assert lexicon.name
        stem = f"{'has' if self.wanted else 'no'}_{lexicon.name}"
        guard = self.when or self.unless
        result = f"{stem}[{'when' if self.when else 'unless'} {guard.name}]" if guard else stem
        assert result
        return result

    def _verdict(self, lexicon: Lexicon, body: str, request: str) -> EvaluationReason:
        spans = lexicon.spans(body)
        holds = lexicon.fires(body) if self.wanted else not spans
        if holds:
            result = EvaluationReason(value=True)
            assert result.reason is None
            return result
        result = EvaluationReason(
            value=False, reason=self._diagnosis(lexicon, spans, body, request)
        )
        assert result.reason is not None
        return result

    def _diagnosis(self, lexicon: Lexicon, spans: list, body: str, request: str) -> str:
        where = f" in {self.field}" if self.field else ""
        lines = []
        if self.wanted:
            examples = ", ".join(lexicon.examples())
            lines.append(f"no {lexicon.name} wording{where}, expected something like: {examples}")
        else:
            terms = ", ".join(f'"{term}"' for term, _, _ in spans[:3])
            plural = "es" if len(spans) != 1 else ""
            lines.append(f"{len(spans)} {lexicon.name} match{plural}{where}: {terms}")
            lines += [f"  {term} -> {snippet(body, start, end)}" for term, start, end in spans[:2]]
        guard = self.when or self.unless
        if guard is not None:
            matched = ", ".join(f'"{term}"' for term in sorted(guard.hits(request))[:2])
            verb = "the request asked" if self.when else "the request never asked"
            lines.append(f"{verb} for {guard.name}: {matched or 'no match'}")
        if lexicon.fix:
            lines.append(f"fix: {lexicon.fix}")
        result = "\n".join(lines)
        assert result, "_diagnosis always appends at least one line"
        assert not lexicon.fix or result.endswith(lexicon.fix)
        return result


@dataclass
class Observe(Evaluator):
    lexicons: Sequence[Lexicon]
    field: str = ""
    of: Literal["output", "inputs"] = "output"

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, str]:
        assert self.lexicons, "Observe needs at least one lexicon"
        body = text_at(ctx.output if self.of == "output" else ctx.inputs, self.field)
        if not body.strip():
            return SKIP
        result = {lexicon.name: lexicon.signal(body).value for lexicon in self.lexicons}
        assert set(result) == {lexicon.name for lexicon in self.lexicons}
        return result
