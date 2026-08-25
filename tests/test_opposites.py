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

# Pairs promoted to a full mirror: each pole rules out *every* one of the other's indicators, so
# adding a term to one pole automatically cancels the other and the two can never drift. A pair
# earns this once its indicators are specific enough that each is a safe blocker for the opposite
# (see the "priority" note in words/request.py). The rest stay in OPPOSITES with the weaker
# two-way check until their indicators are tightened.
MIRRORED: list[tuple[Lexicon, Lexicon]] = [
    (HighPriority, LowPriority),
]

mirror_ids = [f"{a.name}/{b.name}" for a, b in MIRRORED]


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


@pytest.mark.parametrize(("a", "b"), MIRRORED, ids=mirror_ids)
def test_mirrored_pairs_rule_out_every_opposite_term(a: Lexicon, b: Lexicon):
    # the strong invariant: a full mirror. add a term to either pole and this fails until it is
    # also ruled out by the other — the drift guard the curated subsets could not give.
    missing_from_b = set(a.indicates) - set(b.rules_out)
    missing_from_a = set(b.indicates) - set(a.rules_out)
    assert not missing_from_b, f"{b.name} must rule out {sorted(missing_from_b)}"
    assert not missing_from_a, f"{a.name} must rule out {sorted(missing_from_a)}"


def test_low_priority_is_not_denied_by_its_own_phrase():
    # regression: a bare "priority" indicator (a substring of "low priority") would, once mirrored,
    # make low_priority deny "low priority" itself. "high priority" carries the signal instead.
    assert LowPriority.fires("this is low priority")
    assert HighPriority.denied("this is low priority")
    assert HighPriority.fires("this is high priority, drop everything")
    assert LowPriority.denied("this is high priority, drop everything")
