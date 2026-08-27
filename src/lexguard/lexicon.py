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
    assert pattern.startswith(r"\b"), "every alternative is word-boundary anchored"
    assert pattern.endswith(r"\b"), "every alternative is word-boundary anchored"
    return pattern


def snippet(text: str, start: int, end: int, width: int = 34) -> str:
    assert 0 <= start <= end <= len(text), "span must lie within the text"
    left = max(0, start - width)
    right = min(len(text), end + width)
    body = " ".join(text[left:right].split())
    result = f"{'…' if left else ''}{body}{'…' if right < len(text) else ''}"
    if left:
        assert result.startswith("…"), "a left-trimmed snippet opens with an ellipsis"
    return result


@dataclass(frozen=True)
class Lexicon:
    name: str
    indicates: Collection[str]
    # a one-sentence remedy: what to do when this fires. required, so a verdict is always actionable
    fix: str
    rules_out: Collection[str] = ()
    # a short citation for where the terms come from: dumped by as_code(), rendered next to the
    # lexicon in the docs, and readable at runtime (e.g. an agent citing why a check fired).
    # ignored by equality — two lexicons that match the same way are equal whatever their evidence
    evidence: str = field(default="", compare=False)
    _indicate: str | None = field(init=False, repr=False, compare=False)
    _rule_out: str | None = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        assert self.name, "lexicon must have a name"
        # a bare string is a Collection[str] of characters — reject it loudly rather than tidy it
        # into single-letter terms; callers with raw text split it into a list themselves. this is
        # input validation, so it raises (survives -O) rather than asserting
        if isinstance(self.indicates, str) or isinstance(self.rules_out, str):
            raise TypeError("indicates and rules_out take a list of terms, not a string")
        object.__setattr__(self, "indicates", tidy(self.indicates))
        object.__setattr__(self, "rules_out", tidy(self.rules_out))
        object.__setattr__(self, "fix", " ".join(self.fix.split()))
        assert self.fix, f"{self.name}: lexicon must have a fix"
        object.__setattr__(self, "evidence", " ".join(self.evidence.split()))
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
        assert self.name in result, "repr shows the lexicon name"
        assert str(len(self.indicates)) in result, "repr shows the indicator count"
        return result

    def __or__(self, other: Lexicon | Bundle) -> Bundle:
        members = other.members if isinstance(other, Bundle) else (other,)
        bundle = Bundle(members=(self, *members))
        assert self in bundle.members, "the bundle keeps this lexicon"
        assert len(bundle.members) == len(members) + 1, "the bundle adds exactly this member"
        return bundle

    def signal(self, text: str) -> Signal:
        assert all(word not in self.rules_out for word in self.indicates), (
            "indicators and blockers stay disjoint"
        )
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
            assert not self.denied(text), "present and denied are mutually exclusive"
        if outcome is Signal.absent:
            assert not result, "absent never fires"
        return result

    def denied(self, text: str) -> bool:
        outcome = self.signal(text)
        result = outcome is Signal.denied
        if result:
            assert not self.fires(text), "denied never fires"
        if outcome is Signal.present:
            assert not result, "present is not denied"
        return result

    def hits(self, text: str) -> set[str]:
        words = {word.casefold() for word in re.findall(WORD_PATTERN, text)}
        found = words & {word for word in self.indicates if " " not in word}
        if self._indicate:
            found |= set(re.findall(self._indicate, self._fold(text)))
        assert found.issubset(self.indicates), "hits are drawn from the indicators"
        assert all(term == term.casefold() for term in found), "indicators are casefolded"
        return found

    def spans(self, text: str) -> list[tuple[str, int, int]]:
        found = []
        for term in self.hits(text):
            match = re.search(rf"\b{re.escape(term)}\b", text, re.IGNORECASE)
            if match:
                found.append((term, match.start(), match.end()))
        result = sorted(found, key=lambda span: span[1])
        assert all(0 <= start <= end <= len(text) for _, start, end in result), (
            "every span lies within the text"
        )
        assert result == sorted(result, key=lambda span: span[1]), "spans come back in start order"
        return result

    def examples(self, count: int = 4) -> list[str]:
        assert count > 0, "examples() needs a positive count"
        result = sorted(self.indicates, key=lambda word: (" " not in word, word))[:count]
        assert len(result) <= count, "at most count examples"
        return result

    def guidance(self) -> str:
        """The fix as a standalone message: the readable label, then the remedy.

        For handing back on its own — from a guardrail, a log, an agent retry — where the fix needs
        to name what fired.
        """
        label = self.name.replace("_", " ")
        result = f"{label}: {self.fix}"
        assert label in result, "guidance names the concept that fired"
        return result

    def as_code(self) -> str:
        """A paste-able `Lexicon(...)` expression, terms sorted for byte-identical re-emits.

        Compact — run it through your formatter to lay it out for review.
        """
        fields: dict[str, object] = {"name": self.name, "indicates": sorted(self.indicates)}
        if self.rules_out:
            fields["rules_out"] = sorted(self.rules_out)
        fields["fix"] = self.fix
        if self.evidence:
            fields["evidence"] = self.evidence
        result = "Lexicon(" + ", ".join(f"{key}={value!r}" for key, value in fields.items()) + ")"
        assert result.startswith("Lexicon("), "as_code opens with a Lexicon(...) call"
        assert result.endswith(")"), "as_code closes the Lexicon(...) call"
        assert "name" in fields, "name is always emitted"
        return result

    def absent(self, **guards: Any) -> Any:
        from .rule import Rule

        rule = Rule(lexicons=[self], wanted=False, **guards)
        assert rule.wanted is False, "absent() builds a not-wanted rule"
        assert self in rule.lexicons, "the rule targets this lexicon"
        return rule

    def expected(self, **guards: Any) -> Any:
        from .rule import Rule

        rule = Rule(lexicons=[self], wanted=True, **guards)
        assert rule.wanted is True, "expected() builds a wanted rule"
        assert self in rule.lexicons, "the rule targets this lexicon"
        return rule

    def spec(self, wanted: bool = False, **guards: Any) -> Any:
        from .rulespec import RuleSpec

        result = RuleSpec(lexicons=[self], wanted=wanted, **guards)
        assert result.wanted is wanted, "the spec keeps the wanted flag"
        assert self in result.lexicons, "the spec targets this lexicon"
        return result

    def _any(self, text: str, words: Collection[str], pattern: str | None) -> bool:
        folded = self._fold(text)
        if pattern and re.search(pattern, folded):
            return True
        singles = {word for word in words if " " not in word}
        result = bool({word.casefold() for word in re.findall(WORD_PATTERN, text)} & singles)
        assert singles.issubset(words), "singles are the single-word terms"
        if pattern:
            assert pattern in (self._indicate, self._rule_out), (
                "the phrase pattern belongs to this lexicon"
            )
        return result

    @staticmethod
    def _fold(text: str) -> str:
        assert text is not None, "fold needs text to normalize"
        result = unicodedata.normalize("NFKC", text).casefold()
        # casefold() can decompose what NFKC just composed (e.g. "ῶ"), so result may not stay NFKC
        assert result == result.casefold(), "folded text is stable under a second casefold"
        return result


@dataclass(frozen=True)
class Bundle:
    members: tuple[Lexicon, ...]

    def __or__(self, other: Lexicon | Bundle) -> Bundle:
        extra = other.members if isinstance(other, Bundle) else (other,)
        bundle = Bundle(members=(*self.members, *extra))
        assert set(self.members).issubset(bundle.members), "the merge keeps our members"
        assert len(bundle.members) == len(self.members) + len(extra), "the merge adds the extras"
        return bundle

    def absent(self, **guards: Any) -> Any:
        from .rule import Rule

        rule = Rule(lexicons=list(self.members), wanted=False, **guards)
        assert rule.wanted is False, "absent() builds a not-wanted rule"
        assert set(rule.lexicons) == set(self.members), "the rule spans the bundle's members"
        return rule

    def expected(self, **guards: Any) -> Any:
        from .rule import Rule

        rule = Rule(lexicons=list(self.members), wanted=True, **guards)
        assert rule.wanted is True, "expected() builds a wanted rule"
        assert set(rule.lexicons) == set(self.members), "the rule spans the bundle's members"
        return rule

    def spec(self, wanted: bool = False, **guards: Any) -> Any:
        from .rulespec import RuleSpec

        result = RuleSpec(lexicons=list(self.members), wanted=wanted, **guards)
        assert result.wanted is wanted, "the spec keeps the wanted flag"
        assert set(result.lexicons) == set(self.members), "the spec spans the bundle's members"
        return result

    def signals(self, text: str) -> dict[str, Signal]:
        result = {member.name: member.signal(text) for member in self.members}
        assert set(result) == {member.name for member in self.members}, "one signal per member"
        assert len(result) <= len(self.members), "at most one signal per member"
        return result
