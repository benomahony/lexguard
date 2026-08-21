from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

# GenAI roles map onto the four lexguard groups, so a mined phrase lands in the same group whose
# lexicons already read that role: a system prompt is an instruction, the user turn is the request,
# the model turn is the response, a tool result is external domain text.
GROUP = {
    "system": "instruction",
    "developer": "instruction",
    "user": "request",
    "assistant": "response",
    "choice": "response",
    "tool": "domain",
}

_INDEXED = re.compile(r"^gen_ai\.(prompt|completion)\.(\d+)\.(role|content)$")


@dataclass(frozen=True)
class Message:
    """One turn pulled out of a span, tagged with the lexguard group it belongs to."""

    role: str
    content: str
    group: str

    def __post_init__(self) -> None:
        assert self.group in set(GROUP.values()), f"unknown group {self.group!r}"


@dataclass(frozen=True)
class Trace:
    """Every message across the spans that share a trace id, plus their merged attributes.

    `attributes` is what a `Labeller` and the confounders read: the union of span attributes
    (`gen_ai.request.model`, an eval verdict written back by a judge, a task id, ...). Later spans
    win on a key collision, which keeps response-side attributes over request-side ones.
    """

    trace_id: str
    messages: tuple[Message, ...]
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def text(self, group: str) -> str:
        result = "\n".join(m.content for m in self.messages if m.group == group and m.content)
        assert group in set(GROUP.values())
        return result


def _scalar(value: Any) -> Any:
    # decode a single OTLP anyValue; passthrough for already-decoded plain values
    if not isinstance(value, Mapping):
        return value
    if "stringValue" in value:
        return value["stringValue"]
    if "boolValue" in value:
        return bool(value["boolValue"])
    if "intValue" in value:
        return int(value["intValue"])
    if "doubleValue" in value:
        return float(value["doubleValue"])
    if "arrayValue" in value:
        return [_scalar(item) for item in value["arrayValue"].get("values", [])]
    if "kvlistValue" in value:
        return _attrs(value["kvlistValue"].get("values", []))
    return None


def _attrs(raw: Any) -> dict[str, Any]:
    if isinstance(raw, Mapping):
        return dict(raw)
    result: dict[str, Any] = {}
    for item in raw or []:
        result[item["key"]] = _scalar(item.get("value"))
    return result


def _parts(content: Any) -> str:
    # content can be a plain string, a JSON string, or structured message parts
    if isinstance(content, str):
        stripped = content.strip()
        if stripped[:1] in ("{", "["):
            try:
                return _parts(json.loads(stripped))
            except json.JSONDecodeError:
                return content
        return content
    if isinstance(content, Mapping):
        for key in ("text", "content"):
            if key in content:
                return _parts(content[key])
        return ""
    if isinstance(content, Sequence):
        return " ".join(part for part in (_parts(item) for item in content) if part)
    return ""


def _role(name: str, attrs: Mapping[str, Any]) -> str:
    role = str(attrs.get("role") or "").lower()
    if role in GROUP:
        return role
    tail = name.rsplit(".", 2)
    if len(tail) == 3 and tail[2] == "message" and tail[1] in GROUP:
        return tail[1]
    if name == "gen_ai.choice":
        return "choice"
    return role or "assistant"


def _from_events(events: Any) -> list[Message]:
    result: list[Message] = []
    for event in events or []:
        name = event.get("name", "")
        if not (
            name.startswith("gen_ai.") and (name.endswith(".message") or name == "gen_ai.choice")
        ):
            continue
        attrs = _attrs(event.get("attributes"))
        role = _role(name, attrs)
        # a choice event nests its text under `message`; a *.message event carries `content`
        content = _parts(attrs.get("content") or attrs.get("message") or "")
        if content:
            result.append(Message(role=role, content=content, group=GROUP[role]))
    return result


def _from_indexed(attrs: Mapping[str, Any]) -> list[Message]:
    # OpenLLMetry / Traceloop style: gen_ai.prompt.{i}.role / .content, and gen_ai.completion.*
    buckets: dict[tuple[str, int], dict[str, str]] = {}
    for key, value in attrs.items():
        match = _INDEXED.match(key)
        if match:
            kind, index, field_name = match.group(1), int(match.group(2)), match.group(3)
            buckets.setdefault((kind, index), {})[field_name] = str(value)
    result: list[Message] = []
    for (kind, _), entry in sorted(buckets.items()):
        role = (entry.get("role") or ("assistant" if kind == "completion" else "user")).lower()
        role = role if role in GROUP else ("assistant" if kind == "completion" else "user")
        content = _parts(entry.get("content", ""))
        if content:
            result.append(Message(role=role, content=content, group=GROUP[role]))
    return result


def _from_messages_attr(attrs: Mapping[str, Any]) -> list[Message]:
    # newer semconv: gen_ai.input.messages / gen_ai.output.messages as a JSON array of {role, ...}
    result: list[Message] = []
    for key in ("gen_ai.input.messages", "gen_ai.output.messages"):
        raw = attrs.get(key)
        if raw is None:
            continue
        payload = json.loads(raw) if isinstance(raw, str) else raw
        for entry in payload or []:
            role = str(entry.get("role") or "").lower()
            role = (
                role
                if role in GROUP
                else ("assistant" if key.endswith("output.messages") else "user")
            )
            content = _parts(entry.get("parts") if "parts" in entry else entry.get("content", ""))
            if content:
                result.append(Message(role=role, content=content, group=GROUP[role]))
    return result


def messages_from_span(span: Mapping[str, Any]) -> list[Message]:
    """Pull every message out of one span, trying each GenAI content convention in turn."""
    attrs = _attrs(span.get("attributes"))
    result = _from_events(span.get("events"))
    result += _from_indexed(attrs)
    result += _from_messages_attr(attrs)
    return result


def extract_traces(payload: Any) -> list[Trace]:
    """Turn an OTLP trace export into `Trace` objects keyed by trace id.

    Accepts the OTLP/JSON shape (`{"resourceSpans": [...]}`), a bare list of resourceSpans, or a
    plain list of span mappings. Spans without any GenAI message content are still folded in for
    their attributes, so a labelling span that only carries an eval verdict is not lost.
    """
    spans = _spans(payload)
    order: list[str] = []
    messages: dict[str, list[Message]] = {}
    attributes: dict[str, dict[str, Any]] = {}
    for span in spans:
        trace_id = str(span.get("traceId") or span.get("trace_id") or "")
        if trace_id not in messages:
            order.append(trace_id)
            messages[trace_id] = []
            attributes[trace_id] = {}
        messages[trace_id].extend(messages_from_span(span))
        attributes[trace_id].update(_attrs(span.get("attributes")))
    result = [
        Trace(trace_id=tid, messages=tuple(messages[tid]), attributes=attributes[tid])
        for tid in order
    ]
    assert len(result) == len(order)
    return result


def _spans(payload: Any) -> list[Mapping[str, Any]]:
    if isinstance(payload, Mapping) and "resourceSpans" in payload:
        payload = payload["resourceSpans"]
    result: list[Mapping[str, Any]] = []
    for item in payload or []:
        if isinstance(item, Mapping) and "scopeSpans" in item:
            for scope in item["scopeSpans"]:
                result.extend(scope.get("spans", []))
        elif isinstance(item, Mapping) and "spans" in item:
            result.extend(item["spans"])
        elif isinstance(item, Mapping):
            result.append(item)
    return result
