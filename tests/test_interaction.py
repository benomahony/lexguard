from __future__ import annotations

import pytest

from lexguard import Frustration, Rejection, ScopeCreep, Stuck, UnverifiedClaim

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


def test_scope_creep_is_ruled_out_when_the_extra_was_asked_for():
    assert ScopeCreep.denied("i also updated the config as you asked")
    assert ScopeCreep.denied("also added the test you asked me to")


def test_stuck_fires_on_retry_and_dead_end_language():
    assert Stuck.matches("i'm stuck, i've tried everything and nothing i try works")
    assert Stuck.matches("same error again, going in circles here")
    assert not Stuck.matches("straightforward change, one line")


def test_stuck_is_ruled_out_by_recovery():
    assert Stuck.denied("i was stuck on this but finally got it working")
    assert Stuck.denied("tried everything, then solved it")
