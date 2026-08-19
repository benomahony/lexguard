from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from .lexicon import Lexicon, snippet

SKIP: dict[str, Any] = {}


def read(obj: Any, path: str) -> list[Any]:
    if not path:
        return [obj] if obj is not None else []
    head, _, rest = path.partition(".")
    many = head.endswith("[]")
    key = head[:-2] if many else head
    value = obj.get(key) if isinstance(obj, Mapping) else getattr(obj, key, None)
    if value is None:
        return []
    if many:
        return [item for element in value for item in read(element, rest)]
    return read(value, rest)


def text_at(obj: Any, path: str) -> str:
    return " ".join(str(value) for value in read(obj, path)) if path else str(obj)


@dataclass
class Rule(Evaluator):
    lexicons: Sequence[Lexicon]
    wanted: bool = False
    when: Lexicon | None = None
    unless: Lexicon | None = None
    field: str = ""
    of: Literal["output", "inputs"] = "output"

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, EvaluationReason]:
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
        stem = f"{'has' if self.wanted else 'no'}_{lexicon.name}"
        guard = self.when or self.unless
        return f"{stem}[{'when' if self.when else 'unless'} {guard.name}]" if guard else stem

    def _verdict(self, lexicon: Lexicon, body: str, request: str) -> EvaluationReason:
        spans = lexicon.spans(body)
        holds = lexicon.fires(body) if self.wanted else not spans
        if holds:
            return EvaluationReason(value=True)
        return EvaluationReason(value=False, reason=self._diagnosis(lexicon, spans, body, request))

    def _diagnosis(self, lexicon: Lexicon, spans: list, body: str, request: str) -> str:
        where = f" in {self.field}" if self.field else ""
        lines = []
        if self.wanted:
            lines.append(f"no {lexicon.name} wording{where}, expected something like: {', '.join(lexicon.examples())}")
        else:
            terms = ", ".join(f'"{term}"' for term, _, _ in spans[:3])
            lines.append(f"{len(spans)} {lexicon.name} match{'es' if len(spans) != 1 else ''}{where}: {terms}")
            lines += [f"  {term} -> {snippet(body, start, end)}" for term, start, end in spans[:2]]
        guard = self.when or self.unless
        if guard is not None:
            matched = ", ".join(f'"{term}"' for term in sorted(guard.hits(request))[:2])
            verb = "the request asked" if self.when else "the request never asked"
            lines.append(f"{verb} for {guard.name}: {matched or 'no match'}")
        if lexicon.fix:
            lines.append(f"fix: {lexicon.fix}")
        return "\n".join(lines)


@dataclass
class Observe(Evaluator):
    lexicons: Sequence[Lexicon]
    field: str = ""
    of: Literal["output", "inputs"] = "output"

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, str]:
        body = text_at(ctx.output if self.of == "output" else ctx.inputs, self.field)
        if not body.strip():
            return SKIP
        return {lexicon.name: lexicon.signal(body).value for lexicon in self.lexicons}
