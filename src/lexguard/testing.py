from __future__ import annotations

from dataclasses import dataclass

from lexguard.lexicon import Lexicon, Signal

__all__ = ["Case", "Expectation", "Mismatch", "Report", "expect"]


@dataclass(frozen=True)
class Case:
    """One example and the outcome it is expected to produce: a `Signal` when the raw
    present/denied/absent call is what's under test, a `bool` when it's the pass/fail `verdict`.
    """

    text: str
    want: Signal | bool


@dataclass(frozen=True)
class Mismatch:
    """One example that did not behave as declared, with the outcome asked for and the one seen."""

    text: str
    want: str
    got: str


@dataclass(frozen=True)
class Report:
    """The outcome of checking every case in an `Expectation`: which ones broke, and how many."""

    name: str
    total: int
    mismatches: tuple[Mismatch, ...] = ()

    def __post_init__(self) -> None:
        assert self.total >= len(self.mismatches), "a mismatch is one of the checked cases"

    @property
    def ok(self) -> bool:
        result = not self.mismatches
        assert result == (len(self.mismatches) == 0), "ok holds exactly when nothing mismatched"
        return result

    def __str__(self) -> str:
        if self.ok:
            return f"{self.name}: all {self.total} expectations hold"
        head = f"{self.name}: {len(self.mismatches)} of {self.total} expectations failed"
        lines = [head]
        lines += [f"  want {m.want}, got {m.got}: {m.text!r}" for m in self.mismatches]
        result = "\n".join(lines)
        assert result.startswith(self.name), "the report names the lexicon it's about"
        return result


def _outcome(lexicon: Lexicon, case: Case) -> Mismatch | None:
    # a Signal case tests the three-valued signal(); a bool case tests verdict().passed. StrEnum
    # members are not bool instances, so the type of `want` alone says which call to make.
    if isinstance(case.want, Signal):
        got = lexicon.signal(case.text)
        return None if got is case.want else Mismatch(case.text, case.want.value, got.value)
    passed = lexicon.verdict(case.text).passed
    if passed is case.want:
        return None
    labels = {True: "pass", False: "fail"}
    return Mismatch(case.text, labels[case.want], labels[passed])


@dataclass(frozen=True)
class Expectation:
    """A lexicon paired with the examples it should classify, built up fluently and checked in one
    go. Immutable: every method returns a new `Expectation` with the cases appended, so a chain
    reads as one declaration and nothing is checked until `.check()` or `.report()`.
    """

    lexicon: Lexicon
    cases: tuple[Case, ...] = ()

    def _add(self, texts: tuple[str, ...], want: Signal | bool) -> Expectation:
        added = tuple(Case(text, want) for text in texts)
        result = Expectation(self.lexicon, self.cases + added)
        assert len(result.cases) == len(self.cases) + len(texts), "each text adds one case"
        return result

    def present(self, *texts: str) -> Expectation:
        """The concept fires cleanly on each text — `signal` is `present`."""
        return self._add(texts, Signal.present)

    def denied(self, *texts: str) -> Expectation:
        """The concept is worded but ruled back out on each text — `signal` is `denied`."""
        return self._add(texts, Signal.denied)

    def absent(self, *texts: str) -> Expectation:
        """The concept is never mentioned on each text — `signal` is `absent`."""
        return self._add(texts, Signal.absent)

    def passes(self, *texts: str) -> Expectation:
        """Each text passes this lexicon's `verdict`, whichever way `fail_when_neutral` points."""
        return self._add(texts, True)

    def fails(self, *texts: str) -> Expectation:
        """Each text fails this lexicon's `verdict`, whichever way `fail_when_neutral` points."""
        return self._add(texts, False)

    def report(self) -> Report:
        """Check every case and collect what broke, without raising."""
        mismatches = tuple(m for case in self.cases if (m := _outcome(self.lexicon, case)))
        result = Report(self.lexicon.name, len(self.cases), mismatches)
        assert result.total == len(self.cases), "the report counts every declared case"
        return result

    def check(self) -> None:
        """Raise `AssertionError` naming every case that broke; return `None` when all hold. Drops
        straight into a pytest test, a doctest, or a `__main__` block.
        """
        report = self.report()
        if not report.ok:
            raise AssertionError(str(report))


def expect(lexicon: Lexicon) -> Expectation:
    """Start an expectation for `lexicon`: `expect(Politeness).present(...).absent(...).check()`."""
    result = Expectation(lexicon)
    assert result.lexicon is lexicon, "the expectation is about the lexicon it was given"
    assert not result.cases, "a fresh expectation carries no cases yet"
    return result
