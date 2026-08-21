from __future__ import annotations

from collections.abc import Callable, Collection
from enum import StrEnum
from typing import Any

from .traces import Trace


class Label(StrEnum):
    success = "success"
    failure = "failure"
    abstain = "abstain"  # the signal did not apply; the trace is dropped from the mine


# A signal is anything that maps a trace to an outcome: a live LLM judge, a stored eval verdict,
# a heuristic. Returning None (or Label.abstain) drops the trace, mirroring a lexicon that records
# nothing when it does not apply.
Labeller = Callable[[Trace], "Label | bool | str | None"]

_TRUE = frozenset({"success", "pass", "passed", "true", "1", "ok", "correct", "yes"})
_FALSE = frozenset({"failure", "fail", "failed", "false", "0", "error", "incorrect", "no"})


def normalize(value: Label | bool | str | int | float | None) -> Label:
    """Coerce whatever a `Labeller` returns into a `Label`, so judges can be terse."""
    if value is None:
        return Label.abstain
    if isinstance(value, Label):
        return value
    if isinstance(value, bool):
        return Label.success if value else Label.failure
    if isinstance(value, (int, float)):
        return Label.success if value else Label.failure
    token = str(value).strip().lower()
    if token in _TRUE:
        return Label.success
    if token in _FALSE:
        return Label.failure
    return Label.abstain


def from_attribute(
    key: str,
    *,
    success: Collection[Any] = (True, "success", "pass"),
    failure: Collection[Any] = (False, "failure", "fail"),
) -> Labeller:
    """Read the outcome a judge already wrote onto the trace, e.g. `from_attribute("eval.passed")`.

    Use this when an offline LLM judge or eval run has stamped its verdict into a span attribute.
    For a live judge, pass your own callable instead — any `Trace -> outcome` function is a valid
    `Labeller`.
    """
    wins = frozenset(str(value).lower() for value in success)
    losses = frozenset(str(value).lower() for value in failure)

    def label(trace: Trace) -> Label:
        raw = trace.attributes.get(key)
        if raw is None:
            return Label.abstain
        token = str(raw).lower()
        if token in wins:
            return Label.success
        if token in losses:
            return Label.failure
        return normalize(raw)

    return label
