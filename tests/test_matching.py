from __future__ import annotations

import pytest

from lexguard import (
    Actionable,
    Apology,
    Approximation,
    CitationDemand,
    ClockTime,
    Completion,
    Correction,
    DueDate,
    Frustration,
    OpinionDemand,
    Question,
    Recurrence,
    Rejection,
    ScopeCreep,
    SelfAssigned,
    Stuck,
    UnverifiedClaim,
)
from lexguard.lexicon import Lexicon

pytestmark = pytest.mark.unit


def test_rejection_fires_on_repudiating_a_prior_turn():
    assert Rejection.matches("no that's wrong, that's not what i asked")
    assert Rejection.matches("you misunderstood, this is wrong")
    assert not Rejection.matches("great, that works perfectly")


def test_rejection_is_ruled_out_by_benign_no():
    assert Rejection.denied("no worries, take your time")
    assert Rejection.denied("no rush at all")
    assert Rejection.denied("no worries, that didn't work but it's fine")


def test_rejection_is_speaker_agnostic():
    assert Rejection.matches("that's not right, you got it wrong")


def test_frustration_fires_on_repetition_and_profanity():
    assert Frustration.matches("i already told you, how many times do i have to say this")
    assert Frustration.matches("this is fucking broken again")
    assert not Frustration.matches("looks good, thanks for the help")


def test_frustration_is_ruled_out_by_positive_profanity():
    assert Frustration.denied("that's fucking brilliant")
    assert Frustration.denied("damn good work")
    assert Frustration.denied("fucking great, that fixed it")


def test_unverified_claim_fires_on_bald_success_claims():
    assert UnverifiedClaim.matches("fixed it, problem solved")
    assert UnverifiedClaim.matches("this fixes it, everything works now")
    assert not UnverifiedClaim.matches("here is the change to the parser")


def test_unverified_claim_is_ruled_out_by_hedges():
    assert UnverifiedClaim.denied("i think this fixes it")
    assert UnverifiedClaim.denied("this should work now")


def test_unverified_claim_is_ruled_out_by_having_run_it():
    assert UnverifiedClaim.denied("i ran the tests and it works now")
    assert UnverifiedClaim.denied("verified, the bug is fixed")


def test_scope_creep_fires_on_unrequested_work():
    assert ScopeCreep.matches("i also refactored the config while i was at it")
    assert ScopeCreep.matches("as a bonus i took the liberty of renaming the module")
    assert not ScopeCreep.matches("here is the fix for the parser bug")


def test_scope_creep_not_masked_by_requested_wording():
    assert ScopeCreep.matches(
        "as requested i fixed the parser; while i was at it i also refactored the config"
    )


def test_stuck_fires_on_retry_and_dead_end_language():
    assert Stuck.matches("i'm stuck, i've tried everything and nothing i try works")
    assert Stuck.matches("same error again, going in circles here")
    assert not Stuck.matches("straightforward change, one line")


def test_stuck_is_ruled_out_by_recovery():
    assert Stuck.denied("i was stuck on this but finally got it working")
    assert Stuck.denied("tried everything, then solved it")


DENIAL_CASES: list[tuple[Lexicon, str, str]] = [
    (Correction, "scratch that, use a set instead", "as i said, keep it as is"),
    (DueDate, "email me tomorrow", "reply whenever, no rush"),
    (Recurrence, "water the plants every day", "just once is fine"),
    (ClockTime, "call at noon", "any time is fine"),
    (Approximation, "get there about 3pm", "arrive at 3pm exactly"),
    (Completion, "already done, all sorted", "it's not done yet"),
    (Actionable, "book the table for two", "just wondering, no action needed"),
    (SelfAssigned, "note to self, pay the rent", "sort it out on behalf of me"),
    (Question, "what time is the meeting", "what should i add to the list"),
    (CitationDemand, "cite your sources for that", "off the top of your head is fine"),
    (OpinionDemand, "what do you think we should do", "just the facts, no opinions"),
    (Apology, "sorry for the delay", "sorry not sorry"),
]


@pytest.mark.parametrize(
    ("lexicon", "fires", "denied"), DENIAL_CASES, ids=[case[0].name for case in DENIAL_CASES]
)
def test_indicator_fires_and_blocker_denies(lexicon: Lexicon, fires: str, denied: str):
    assert lexicon.matches(fires), f"{lexicon.name} should fire on {fires!r}"
    assert lexicon.denied(denied), f"{lexicon.name} should be denied on {denied!r}"
