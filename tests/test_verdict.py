from __future__ import annotations

import pytest

from lexguard import Confirmation, Politeness, Verdict
from lexguard.words.response import Slop

pytestmark = pytest.mark.unit


def test_absent_passes_when_the_lexicon_never_fires():
    assert Slop.verdict("caching skips repeated work") == Verdict(passed=True)


def test_absent_fails_when_the_lexicon_fires():
    verdict = Slop.verdict("let us delve into the intricate tapestry")
    assert verdict.passed is False
    assert '"delve"' in verdict.reason
    assert verdict.reason.endswith(Slop.fix)


def test_fail_when_neutral_flips_the_rule_to_require_a_match():
    assert Confirmation.fail_when_neutral is True
    assert Confirmation.verdict("yes, confirmed, go ahead").passed is True
    assert Confirmation.verdict("lets grab lunch tomorrow").passed is False
    assert Confirmation.verdict("maybe, not sure yet").passed is False


def test_blank_text_passes_an_absent_check_trivially():
    assert Slop.verdict("").passed is True


def test_lexicon_is_callable_as_a_bool():
    assert Politeness("please") is True
    assert Politeness("please fuck off") is False
