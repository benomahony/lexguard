"""Opposite lexicons are plain hand-written data — nothing wires them together.

These tests are the guard instead: they declare which lexicons are opposite poles of one axis
and check the invariants by hand, so the two lists staying consistent is enforced without any
runtime coupling or derived `rules_out`. Adding a pair here documents the intent and catches
drift; it deliberately does not force each pole to rule out *every* term of the other (the
shipped `rules_out` are curated subsets, not full mirrors).
"""

from __future__ import annotations

import pytest

from lexguard import (
    Confirmation,
    CreativeDemand,
    FactualDemand,
    FormatList,
    FormatProse,
    HardDeadline,
    Hedging,
    HighPriority,
    Hypothetical,
    LengthLong,
    LengthShort,
    LowPriority,
    Overclaim,
    SoftDeadline,
    ToneCasual,
    ToneFormal,
)
from lexguard.lexicon import Lexicon

pytestmark = pytest.mark.unit

OPPOSITES: list[tuple[Lexicon, Lexicon]] = [
    (Hedging, Overclaim),
    (HighPriority, LowPriority),
    (HardDeadline, SoftDeadline),
    (Confirmation, Hypothetical),
    (FormatList, FormatProse),
    (LengthShort, LengthLong),
    (ToneFormal, ToneCasual),
    (FactualDemand, CreativeDemand),
]

ids = [f"{a.name}/{b.name}" for a, b in OPPOSITES]


@pytest.mark.parametrize(("a", "b"), OPPOSITES, ids=ids)
def test_poles_share_no_indicator(a: Lexicon, b: Lexicon):
    # a term that indicates both poles of one axis is a bug in one of the two lists
    shared = set(a.indicates) & set(b.indicates)
    assert not shared, f"{a.name} and {b.name} both indicate {sorted(shared)}"


@pytest.mark.parametrize(("a", "b"), OPPOSITES, ids=ids)
def test_each_pole_rules_out_some_of_the_other(a: Lexicon, b: Lexicon):
    # opposition must run both ways: each pole cancels at least one of the other's terms, so
    # wording that mixes the two resolves to denied rather than firing one side
    assert set(a.indicates) & set(b.rules_out), f"{b.name} rules out none of {a.name}"
    assert set(b.indicates) & set(a.rules_out), f"{a.name} rules out none of {b.name}"


@pytest.mark.parametrize(("a", "b"), OPPOSITES, ids=ids)
def test_mixing_both_poles_is_denied(a: Lexicon, b: Lexicon):
    # take a term each side actually cancels on the other, and confirm the mix denies both
    a_term = next(iter(set(a.indicates) & set(b.rules_out)))
    b_term = next(iter(set(b.indicates) & set(a.rules_out)))
    mixed = f"{a_term} {b_term}"
    assert a.denied(mixed), f"{a.name} not denied by {mixed!r}"
    assert b.denied(mixed), f"{b.name} not denied by {mixed!r}"
