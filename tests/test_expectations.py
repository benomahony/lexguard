from __future__ import annotations

import pytest

from lexguard import HardDeadline, Politeness, SoftDeadline
from lexguard.testing import Case, Expectation, Report, expect
from lexguard.words.style import Slop

pytestmark = pytest.mark.unit


def test_a_satisfied_chain_checks_clean():
    expect(Politeness).present("could you send this over when you get a sec?").absent(
        "send me the report"
    ).denied("could you please fix the fucking bug").check()


def test_expect_starts_empty_and_is_immutable():
    start = expect(Slop)
    assert start.cases == ()
    grown = start.present("let us delve in")
    assert start.cases == (), "the original expectation is untouched"
    assert grown.cases == (Case("let us delve in", start.lexicon.signal("let us delve in")),)
    assert isinstance(grown, Expectation)


def test_report_names_the_broken_case_and_leaves_the_rest():
    report = expect(Slop).present("let us delve in").present("a plain sentence").report()
    assert isinstance(report, Report)
    assert report.total == 2
    assert not report.ok
    assert [(m.text, m.want, m.got) for m in report.mismatches] == [
        ("a plain sentence", "present", "absent")
    ]


def test_a_clean_report_is_ok_and_has_no_mismatches():
    report = expect(Slop).absent("caching skips repeated work").report()
    assert report.ok
    assert report.mismatches == ()
    assert str(report) == "slop: all 1 expectations hold"


def test_check_raises_with_the_full_diagnostic():
    with pytest.raises(AssertionError) as caught:
        expect(Slop).absent("let us delve into the tapestry").check()
    message = str(caught.value)
    assert message.startswith("slop: 1 of 1 expectations failed")
    assert "want absent, got present" in message
    assert "let us delve into the tapestry" in message


def test_passes_and_fails_follow_fail_when_neutral():
    assert Politeness.fail_when_neutral is True
    expect(Politeness).passes("thanks, could you take a look").fails("send me the report").check()


def test_a_broken_verdict_expectation_reads_as_pass_fail():
    report = expect(Politeness).passes("send me the report").report()
    assert [(m.want, m.got) for m in report.mismatches] == [("pass", "fail")]


def test_it_expresses_a_mirrored_family_denial():
    expect(HardDeadline).present("this must be in by friday").denied("ideally by friday").check()
    expect(SoftDeadline).present("ideally friday").denied("hard deadline: friday").check()
