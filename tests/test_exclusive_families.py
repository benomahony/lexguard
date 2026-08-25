"""Mutually-exclusive lexicon families, guarded by hand rather than by a runtime abstraction.

A family is a set of lexicons that are mutually exclusive: no text truly exhibits two at once —
one output format, one priority, one deadline hardness. We do *not* require the family to be
exhaustive; a task can be medium priority, hitting no member, which is a correct `absent` on all
of them. What we require is:

- **disjoint indicators** — no term indicates two members (always enforced); and
- for a `mirror=True` family, a **full mirror** — each member rules out every other member's
  indicators, so any mix denies all of them and the lists cannot drift.

A family earns `mirror=True` once its indicators are faithful enough that each is a safe blocker
for its siblings: specific enough that its mere presence entails the member (see the "priority"
note in words/request.py). A bare, ambiguous word — a genus shared with a sibling, like the bare
"priority" that is a substring of "low priority" — must be sharpened first. Families still at
`mirror=False` are declared mutually exclusive and kept disjoint, with the mirror pending that
tightening.
"""

from __future__ import annotations

import itertools
from typing import NamedTuple

import pytest

from lexguard import (
    Confirmation,
    CreativeDemand,
    FactualDemand,
    FormatCode,
    FormatList,
    FormatProse,
    FormatTable,
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


class Family(NamedTuple):
    name: str
    members: tuple[Lexicon, ...]
    mirror: bool


FAMILIES: list[Family] = [
    Family("priority", (HighPriority, LowPriority), mirror=True),
    Family("format", (FormatList, FormatTable, FormatProse, FormatCode), mirror=False),
    Family("length", (LengthShort, LengthLong), mirror=False),
    Family("tone", (ToneFormal, ToneCasual), mirror=False),
    Family("deadline", (HardDeadline, SoftDeadline), mirror=False),
    Family("decision", (Confirmation, Hypothetical), mirror=False),
    Family("mode", (FactualDemand, CreativeDemand), mirror=False),
]

family_ids = [family.name for family in FAMILIES]
mirror_families = [family for family in FAMILIES if family.mirror]
mirror_ids = [family.name for family in mirror_families]


@pytest.mark.parametrize("family", FAMILIES, ids=family_ids)
def test_members_share_no_indicator(family: Family):
    # a term that indicates two members of one exclusive family is a bug in one of the lists
    for a, b in itertools.combinations(family.members, 2):
        shared = set(a.indicates) & set(b.indicates)
        assert not shared, f"{family.name}: {a.name} and {b.name} both indicate {sorted(shared)}"


@pytest.mark.parametrize("family", mirror_families, ids=mirror_ids)
def test_mirror_family_rules_out_every_sibling_term(family: Family):
    # the strong invariant: add a term to any member and this fails until every sibling rules it
    # out. this is the drift guard the curated subsets could not give.
    for member in family.members:
        siblings: set[str] = set().union(
            *(set(other.indicates) for other in family.members if other is not member)
        )
        missing = siblings - set(member.rules_out)
        assert not missing, f"{family.name}: {member.name} must rule out {sorted(missing)}"


@pytest.mark.parametrize("family", mirror_families, ids=mirror_ids)
def test_mixing_two_members_denies_both(family: Family):
    for a, b in itertools.combinations(family.members, 2):
        mixed = f"{next(iter(a.indicates))} {next(iter(b.indicates))}"
        assert a.denied(mixed), f"{family.name}: {a.name} not denied by {mixed!r}"
        assert b.denied(mixed), f"{family.name}: {b.name} not denied by {mixed!r}"


def test_low_priority_is_not_denied_by_its_own_phrase():
    # regression: a bare "priority" indicator (a substring of "low priority") would, once mirrored,
    # make low_priority deny "low priority" itself. "high priority" carries the signal instead.
    assert LowPriority.fires("this is low priority")
    assert HighPriority.denied("this is low priority")
    assert HighPriority.fires("this is high priority, drop everything")
    assert LowPriority.denied("this is high priority, drop everything")


def test_hedging_overclaim_are_disjoint_and_cancel_but_are_not_a_mirror_family():
    # Hedging and Overclaim are opposite *per claim*, but a text holds many claims, so a hedge
    # about X and a booster about Y coexist — they are not mutually exclusive at the granularity
    # the matcher runs on (the whole text). So they are deliberately not a mirror family: kept
    # disjoint and cancelling on their core terms, curated by hand rather than fully mirrored.
    assert set(Hedging.indicates).isdisjoint(Overclaim.indicates)
    assert set(Hedging.indicates) & set(Overclaim.rules_out), (
        "overclaim should rule out some hedges"
    )
    assert set(Overclaim.indicates) & set(Hedging.rules_out), (
        "hedging should rule out some boosters"
    )
