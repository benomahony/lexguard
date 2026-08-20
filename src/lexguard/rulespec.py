from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from .lexicon import Lexicon, snippet


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


@dataclass(frozen=True)
class Verdict:
    """A single lexicon's pass/fail outcome, independent of any eval framework."""

    name: str
    passed: bool
    reason: str | None = None

    def __post_init__(self) -> None:
        assert self.name, "a Verdict needs a name"
        assert self.passed or self.reason is not None, "a failing Verdict must carry a reason"


@dataclass(frozen=True)
class RuleSpec:
    """The framework-agnostic core behind `Lexicon.spec()` / `Bundle.spec()`.

    `check()` is the whole surface: hand it an output and the originating input, get back the
    per-lexicon verdicts, or `None` when a guard or empty field means the rule did not apply.
    Every eval-framework adapter (pydantic-evals, DeepEval, Inspect AI, ...) is a thin wrapper
    around this.
    """

    lexicons: Sequence[Lexicon]
    wanted: bool = False
    when: Lexicon | None = None
    unless: Lexicon | None = None
    field: str = ""
    of: Literal["output", "inputs"] = "output"

    def __post_init__(self) -> None:
        assert self.lexicons, "RuleSpec needs at least one lexicon"
        assert not (self.when and self.unless), "a RuleSpec cannot have both when and unless"

    def check(self, output: Any, inputs: Any) -> list[Verdict] | None:
        request = str(inputs)
        if self.when is not None and not self.when.fires(request):
            return None
        if self.unless is not None and self.unless.fires(request):
            return None
        body = text_at(output if self.of == "output" else inputs, self.field)
        if not body.strip():
            return None
        result = [self._verdict(entry, body, request) for entry in self.lexicons]
        assert len(result) == len(self.lexicons)
        return result

    def _name(self, lexicon: Lexicon) -> str:
        assert lexicon.name
        stem = f"{'has' if self.wanted else 'no'}_{lexicon.name}"
        guard = self.when or self.unless
        result = f"{stem}[{'when' if self.when else 'unless'} {guard.name}]" if guard else stem
        assert result
        return result

    def _verdict(self, lexicon: Lexicon, body: str, request: str) -> Verdict:
        spans = lexicon.spans(body)
        holds = lexicon.fires(body) if self.wanted else not spans
        name = self._name(lexicon)
        if holds:
            return Verdict(name=name, passed=True)
        return Verdict(
            name=name, passed=False, reason=self._diagnosis(lexicon, spans, body, request)
        )

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


@dataclass(frozen=True)
class ObserveSpec:
    """The framework-agnostic core behind pydantic-evals `Observe`: labels, not assertions."""

    lexicons: Sequence[Lexicon]
    field: str = ""
    of: Literal["output", "inputs"] = "output"

    def __post_init__(self) -> None:
        assert self.lexicons, "ObserveSpec needs at least one lexicon"

    def signals(self, output: Any, inputs: Any) -> dict[str, str] | None:
        body = text_at(output if self.of == "output" else inputs, self.field)
        if not body.strip():
            return None
        result = {lexicon.name: lexicon.signal(body).value for lexicon in self.lexicons}
        assert set(result) == {lexicon.name for lexicon in self.lexicons}
        return result
