from __future__ import annotations

import re
import unicodedata
from collections.abc import Collection
from dataclasses import dataclass, field
from enum import StrEnum

WORD_PATTERN = r"[\w']+"


class Signal(StrEnum):
    present = "present"
    denied = "denied"
    absent = "absent"


@dataclass(frozen=True)
class Verdict:
    """A single lexicon's pass/fail outcome, independent of any eval framework."""

    passed: bool
    reason: str | None = None

    def __post_init__(self) -> None:
        if not self.passed:
            assert self.reason is not None, "a failing Verdict must carry a reason"
        else:
            assert self.reason is None, "a passing Verdict carries no reason"


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
    # a one-sentence remedy: what to do on a match. required, so a verdict is always actionable
    fix: str
    rules_out: Collection[str] = ()
    # does verdict() fail when this concept is neutral — absent, never mentioned — rather than
    # when it's present? the lexicon is the domain object, so it, not a per-call flag on some
    # evaluator, owns this judgement. True for a lexicon you want to see (Confirmation,
    # Politeness: silence is the problem). The common case takes the default: Slop and Rudeness
    # are things you don't want, so a match is the problem, not the silence.
    fail_when_neutral: bool = False
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

    @property
    def label(self) -> str:
        """The PascalCase form of `.name` (e.g. `"transition_slop"` -> `"TransitionSlop"`),
        matching the Python identifier it's shipped under. Used as the report/assertion key by
        every eval-framework adapter; `.name` itself stays lowercase for CLI lookup and prose.
        """
        result = "".join(word.capitalize() for word in self.name.split("_"))
        assert result, "a lexicon always has a name to derive a label from"
        assert "_" not in result, "label is PascalCase, with no separators left in it"
        return result

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

    def matches(self, text: str) -> bool:
        """Does `text` match this lexicon: an indicator hit that no blocker rules back out?"""
        outcome = self.signal(text)
        result = outcome is Signal.present
        if result:
            assert not self.denied(text), "present and denied are mutually exclusive"
        if outcome is Signal.absent:
            assert not result, "absent never matches"
        return result

    def __call__(self, text: str) -> bool:
        """`Politeness("please")` — the same answer as `Politeness.matches("please")`."""
        result = self.matches(text)
        assert self.matches(text) is result, "matches is a pure function of the same text"
        assert result == (self.signal(text) is Signal.present), "matches agrees with signal"
        return result

    def verdict(self, text: str) -> Verdict:
        """The pass/fail judgment this lexicon makes about `text`.

        `self.fail_when_neutral` is this lexicon's own call, not a per-call flag: a lexicon for
        something you want present (`Confirmation`, `Politeness`) sets `fail_when_neutral=True`,
        since silence is the failure. The common case, a lexicon for something you don't want
        (`Slop`, `Rudeness`), leaves the default `False` — a match is the failure instead.
        Framework-agnostic; every eval-framework adapter is a thin wrapper around this.
        """
        holds = self.matches(text) == self.fail_when_neutral
        result = (
            Verdict(passed=True) if holds else Verdict(passed=False, reason=self._diagnose(text))
        )
        assert result.passed == holds, "verdict mirrors the fail_when_neutral/actual match"
        assert (result.reason is None) == result.passed, "a reason exists exactly when it failed"
        return result

    def _diagnose(self, text: str) -> str:
        if self.fail_when_neutral:
            examples = ", ".join(self.examples())
            result = f"no {self.name} wording, expected something like: {examples}\nfix: {self.fix}"
            assert self.name in result, "the diagnosis names the lexicon it's about"
            assert result.endswith(self.fix), "the fix is always the last line"
            return result
        spans = self.spans(text)
        terms = ", ".join(f'"{term}"' for term, _, _ in spans[:3])
        plural = "es" if len(spans) != 1 else ""
        lines = [f"{len(spans)} {self.name} match{plural}: {terms}"]
        lines += [f"  {term} -> {snippet(text, start, end)}" for term, start, end in spans[:2]]
        lines.append(f"fix: {self.fix}")
        result = "\n".join(lines)
        assert result.endswith(self.fix), "the fix is always the last line"
        assert self.name in result, "the diagnosis names the lexicon it's about"
        return result

    def denied(self, text: str) -> bool:
        outcome = self.signal(text)
        result = outcome is Signal.denied
        if result:
            assert not self.matches(text), "denied never matches"
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

    def as_code(self) -> str:
        """A paste-able `Lexicon(...)` expression, terms sorted for byte-identical re-emits.

        Compact — run it through your formatter to lay it out for review.
        """
        fields: dict[str, object] = {"name": self.name, "indicates": sorted(self.indicates)}
        if self.rules_out:
            fields["rules_out"] = sorted(self.rules_out)
        fields["fix"] = self.fix
        if self.fail_when_neutral:
            fields["fail_when_neutral"] = self.fail_when_neutral
        if self.evidence:
            fields["evidence"] = self.evidence
        result = "Lexicon(" + ", ".join(f"{key}={value!r}" for key, value in fields.items()) + ")"
        assert result.startswith("Lexicon("), "as_code opens with a Lexicon(...) call"
        assert result.endswith(")"), "as_code closes the Lexicon(...) call"
        assert "name" in fields, "name is always emitted"
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

    def signals(self, text: str) -> dict[str, Signal]:
        result = {member.name: member.signal(text) for member in self.members}
        assert set(result) == {member.name for member in self.members}, "one signal per member"
        assert len(result) <= len(self.members), "at most one signal per member"
        return result
