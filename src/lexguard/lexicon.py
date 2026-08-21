from __future__ import annotations

import re
import unicodedata
from collections.abc import Collection
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

WORD_PATTERN = r"[\w']+"


class Signal(StrEnum):
    present = "present"
    denied = "denied"
    absent = "absent"


def tidy(words: Collection[str]) -> frozenset[str]:
    result = frozenset(" ".join(word.split()).casefold() for word in words if word.strip())
    assert all(word for word in result), "tidy() must drop blank entries"
    assert all(word == word.casefold() for word in result), "tidy() must casefold"
    return result


def phrases(words: Collection[str]) -> str | None:
    multiword = sorted((word for word in words if " " in word), key=len, reverse=True)
    if not multiword:
        return None
    pattern = "|".join(rf"\b{re.escape(word)}\b" for word in multiword)
    # a word containing a literal "|" adds its own escaped "\|", so count() can't check the join
    assert pattern.startswith(r"\b")
    return pattern


def literal(term: str) -> str:
    # a Python string literal for `term`, quoted the way ruff/black would: prefer double
    # quotes, fall back to single only when that escapes fewer inner quotes. Escaping matches
    # repr() so apostrophes ("what's"), backslashes, and control chars all survive eval().
    quote = "'" if term.count('"') > term.count("'") else '"'
    out = [quote]
    for ch in term:
        if ch == quote or ch == "\\":
            out.append("\\" + ch)
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif ch.isprintable():
            out.append(ch)
        elif ord(ch) <= 0xFF:
            out.append(f"\\x{ord(ch):02x}")
        elif ord(ch) <= 0xFFFF:
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(f"\\U{ord(ch):08x}")
    out.append(quote)
    return "".join(out)


def _terms(key: str, terms: Collection[str]) -> str:
    # one term per line, sorted for a deterministic (byte-identical) re-emit, trailing comma so
    # black keeps the list exploded — every term owns a line, so the review diff is one term wide
    ordered = sorted(terms)
    if not ordered:
        return f"    {key}=[],"
    body = "".join(f"        {literal(term)},\n" for term in ordered)
    return f"    {key}=[\n{body}    ],"


def snippet(text: str, start: int, end: int, width: int = 34) -> str:
    assert 0 <= start <= end <= len(text)
    left = max(0, start - width)
    right = min(len(text), end + width)
    body = " ".join(text[left:right].split())
    result = f"{'…' if left else ''}{body}{'…' if right < len(text) else ''}"
    assert left == 0 or result.startswith("…")
    return result


@dataclass(frozen=True)
class Lexicon:
    name: str
    indicates: Collection[str]
    rules_out: Collection[str] = ()
    fix: str = ""
    _indicate: str | None = field(init=False, repr=False, compare=False)
    _rule_out: str | None = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        assert self.name, "lexicon must have a name"
        # a bare string is a Collection[str] of characters — reject it loudly rather than tidy it
        # into single-letter terms; callers with raw text split it into a list themselves
        assert not isinstance(self.indicates, str), "indicates takes a list of terms, not a string"
        assert not isinstance(self.rules_out, str), "rules_out takes a list of terms, not a string"
        object.__setattr__(self, "indicates", tidy(self.indicates))
        object.__setattr__(self, "rules_out", tidy(self.rules_out))
        object.__setattr__(self, "fix", " ".join(self.fix.split()))
        object.__setattr__(self, "_indicate", phrases(self.indicates))
        object.__setattr__(self, "_rule_out", phrases(self.rules_out))
        assert all(word not in self.rules_out for word in self.indicates), (
            f"{self.name}: a phrase cannot both indicate and rule out the same concept"
        )

    def __repr__(self) -> str:
        result = (
            f"Lexicon({self.name}, {len(self.indicates)} indicators, "
            f"{len(self.rules_out)} blockers)"
        )
        assert self.name in result
        assert str(len(self.indicates)) in result
        return result

    def __or__(self, other: Lexicon | Bundle) -> Bundle:
        members = other.members if isinstance(other, Bundle) else (other,)
        bundle = Bundle(members=(self, *members))
        assert self in bundle.members
        assert len(bundle.members) == len(members) + 1
        return bundle

    def signal(self, text: str) -> Signal:
        assert all(word not in self.rules_out for word in self.indicates)
        ruled_out = self._any(text, self.rules_out, self._rule_out)
        if ruled_out:
            return Signal.denied
        indicated = self._any(text, self.indicates, self._indicate)
        result = Signal.present if indicated else Signal.absent
        assert not ruled_out, "denied always takes priority over present/absent"
        return result

    def fires(self, text: str) -> bool:
        outcome = self.signal(text)
        result = outcome is Signal.present
        if result:
            assert not self.denied(text)
        if outcome is Signal.absent:
            assert not result
        return result

    def denied(self, text: str) -> bool:
        outcome = self.signal(text)
        result = outcome is Signal.denied
        if result:
            assert not self.fires(text)
        if outcome is Signal.present:
            assert not result
        return result

    def hits(self, text: str) -> set[str]:
        words = {word.casefold() for word in re.findall(WORD_PATTERN, text)}
        found = words & {word for word in self.indicates if " " not in word}
        if self._indicate:
            found |= set(re.findall(self._indicate, self._fold(text)))
        assert found.issubset(self.indicates)
        assert all(term == term.casefold() for term in found)
        return found

    def spans(self, text: str) -> list[tuple[str, int, int]]:
        found = []
        for term in self.hits(text):
            match = re.search(rf"\b{re.escape(term)}\b", text, re.IGNORECASE)
            if match:
                found.append((term, match.start(), match.end()))
        result = sorted(found, key=lambda span: span[1])
        assert all(0 <= start <= end <= len(text) for _, start, end in result)
        assert result == sorted(result, key=lambda span: span[1])
        return result

    def examples(self, count: int = 4) -> list[str]:
        assert count > 0, "examples() needs a positive count"
        result = sorted(self.indicates, key=lambda word: (" " not in word, word))[:count]
        assert len(result) <= count
        return result

    def as_code(self) -> str:
        """Emit this lexicon as paste-able Python source.

        A lexicon is a judgement artifact: it belongs in code, reviewed and diffed, not
        round-tripped through JSON. This returns a `Lexicon(...)` expression (ruff/black
        formatted, terms sorted so re-emitting is byte-identical) ready to paste into a module.
        """
        lines = ["Lexicon(", f"    name={literal(self.name)},", _terms("indicates", self.indicates)]
        if self.rules_out:
            lines.append(_terms("rules_out", self.rules_out))
        if self.fix:
            lines.append(f"    fix={literal(self.fix)},")
        lines.append(")")
        return "\n".join(lines)

    def absent(self, **guards: Any) -> Any:
        from .rule import Rule

        rule = Rule(lexicons=[self], wanted=False, **guards)
        assert rule.wanted is False
        assert self in rule.lexicons
        return rule

    def expected(self, **guards: Any) -> Any:
        from .rule import Rule

        rule = Rule(lexicons=[self], wanted=True, **guards)
        assert rule.wanted is True
        assert self in rule.lexicons
        return rule

    def spec(self, wanted: bool = False, **guards: Any) -> Any:
        from .rulespec import RuleSpec

        result = RuleSpec(lexicons=[self], wanted=wanted, **guards)
        assert result.wanted is wanted
        assert self in result.lexicons
        return result

    def _any(self, text: str, words: Collection[str], pattern: str | None) -> bool:
        folded = self._fold(text)
        if pattern and re.search(pattern, folded):
            return True
        singles = {word for word in words if " " not in word}
        result = bool({word.casefold() for word in re.findall(WORD_PATTERN, text)} & singles)
        assert singles.issubset(words)
        assert not pattern or pattern in (self._indicate, self._rule_out)
        return result

    @staticmethod
    def _fold(text: str) -> str:
        result = unicodedata.normalize("NFKC", text).casefold()
        # casefold() can decompose what NFKC just composed (e.g. "ῶ"), so result may not stay NFKC
        assert result == result.casefold()
        return result


@dataclass(frozen=True)
class Bundle:
    members: tuple[Lexicon, ...]

    def __or__(self, other: Lexicon | Bundle) -> Bundle:
        extra = other.members if isinstance(other, Bundle) else (other,)
        bundle = Bundle(members=(*self.members, *extra))
        assert set(self.members).issubset(bundle.members)
        assert len(bundle.members) == len(self.members) + len(extra)
        return bundle

    def absent(self, **guards: Any) -> Any:
        from .rule import Rule

        rule = Rule(lexicons=list(self.members), wanted=False, **guards)
        assert rule.wanted is False
        assert set(rule.lexicons) == set(self.members)
        return rule

    def expected(self, **guards: Any) -> Any:
        from .rule import Rule

        rule = Rule(lexicons=list(self.members), wanted=True, **guards)
        assert rule.wanted is True
        assert set(rule.lexicons) == set(self.members)
        return rule

    def spec(self, wanted: bool = False, **guards: Any) -> Any:
        from .rulespec import RuleSpec

        result = RuleSpec(lexicons=list(self.members), wanted=wanted, **guards)
        assert result.wanted is wanted
        assert set(result.lexicons) == set(self.members)
        return result

    def signals(self, text: str) -> dict[str, Signal]:
        result = {member.name: member.signal(text) for member in self.members}
        assert set(result) == {member.name for member in self.members}
        assert len(result) <= len(self.members)
        return result
