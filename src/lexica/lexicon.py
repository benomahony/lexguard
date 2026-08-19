from __future__ import annotations

import re
import unicodedata
from collections.abc import Collection
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

WORD = re.compile(r"[\w']+")


class Signal(StrEnum):
    present = "present"
    denied = "denied"
    absent = "absent"


def tidy(words: Collection[str]) -> frozenset[str]:
    return frozenset(" ".join(word.split()).casefold() for word in words if word.strip())


def phrases(words: Collection[str]) -> re.Pattern[str] | None:
    multiword = sorted((word for word in words if " " in word), key=len, reverse=True)
    if not multiword:
        return None
    return re.compile("|".join(rf"\b{re.escape(word)}\b" for word in multiword))


def snippet(text: str, start: int, end: int, width: int = 34) -> str:
    left = max(0, start - width)
    right = min(len(text), end + width)
    body = " ".join(text[left:right].split())
    return f"{'…' if left else ''}{body}{'…' if right < len(text) else ''}"


@dataclass(frozen=True)
class Lexicon:
    name: str
    indicates: Collection[str]
    rules_out: Collection[str] = ()
    fix: str = ""
    _indicate: re.Pattern[str] | None = field(init=False, repr=False, compare=False)
    _rule_out: re.Pattern[str] | None = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "indicates", tidy(self.indicates))
        object.__setattr__(self, "rules_out", tidy(self.rules_out))
        object.__setattr__(self, "fix", " ".join(self.fix.split()))
        object.__setattr__(self, "_indicate", phrases(self.indicates))
        object.__setattr__(self, "_rule_out", phrases(self.rules_out))

    def __repr__(self) -> str:
        return f"Lexicon({self.name}, {len(self.indicates)} indicators, {len(self.rules_out)} blockers)"

    def __or__(self, other: Lexicon | Bundle) -> Bundle:
        members = other.members if isinstance(other, Bundle) else (other,)
        return Bundle(members=(self, *members))

    def signal(self, text: str) -> Signal:
        if self._any(text, self.rules_out, self._rule_out):
            return Signal.denied
        if self._any(text, self.indicates, self._indicate):
            return Signal.present
        return Signal.absent

    def fires(self, text: str) -> bool:
        return self.signal(text) is Signal.present

    def denied(self, text: str) -> bool:
        return self.signal(text) is Signal.denied

    def hits(self, text: str) -> set[str]:
        words = {word.casefold() for word in WORD.findall(text)}
        found = words & {word for word in self.indicates if " " not in word}
        if self._indicate:
            found |= set(self._indicate.findall(self._fold(text)))
        return found

    def spans(self, text: str) -> list[tuple[str, int, int]]:
        found = []
        for term in self.hits(text):
            match = re.search(rf"\b{re.escape(term)}\b", text, re.IGNORECASE)
            if match:
                found.append((term, match.start(), match.end()))
        return sorted(found, key=lambda span: span[1])

    def examples(self, count: int = 4) -> list[str]:
        return sorted(self.indicates, key=lambda word: (" " not in word, word))[:count]

    def extend(self, indicates: Collection[str] = (), rules_out: Collection[str] = (), fix: str = "") -> Lexicon:
        return Lexicon(
            name=self.name,
            indicates=[*self.indicates, *indicates],
            rules_out=[*self.rules_out, *rules_out],
            fix=fix or self.fix,
        )

    def absent(self, **guards: Any) -> Any:
        from .rule import Rule

        return Rule(lexicons=[self], wanted=False, **guards)

    def expected(self, **guards: Any) -> Any:
        from .rule import Rule

        return Rule(lexicons=[self], wanted=True, **guards)

    def _any(self, text: str, words: Collection[str], pattern: re.Pattern[str] | None) -> bool:
        if pattern and pattern.search(self._fold(text)):
            return True
        singles = {word for word in words if " " not in word}
        return bool({word.casefold() for word in WORD.findall(text)} & singles)

    @staticmethod
    def _fold(text: str) -> str:
        return unicodedata.normalize("NFKC", text).casefold()


@dataclass(frozen=True)
class Bundle:
    members: tuple[Lexicon, ...]

    def __or__(self, other: Lexicon | Bundle) -> Bundle:
        extra = other.members if isinstance(other, Bundle) else (other,)
        return Bundle(members=(*self.members, *extra))

    def absent(self, **guards: Any) -> Any:
        from .rule import Rule

        return Rule(lexicons=list(self.members), wanted=False, **guards)

    def expected(self, **guards: Any) -> Any:
        from .rule import Rule

        return Rule(lexicons=list(self.members), wanted=True, **guards)

    def signals(self, text: str) -> dict[str, Signal]:
        return {member.name: member.signal(text) for member in self.members}
