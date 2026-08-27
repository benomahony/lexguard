from __future__ import annotations

import pytest
from pydantic_evals import Case, Dataset

from lexguard import (
    AdviceDemand,
    CitationDemand,
    CitationMarker,
    Disclaimer,
    HighPriority,
    NoCaveats,
    Observe,
    Politeness,
    Preamble,
    Servility,
    Sycophancy,
)
from lexguard.words.response import Slop

pytestmark = pytest.mark.unit


def run(evaluators: list, prompt: str, reply: str):
    dataset = Dataset(name="d", cases=[Case(inputs=prompt)], evaluators=evaluators)

    async def task(text: str) -> str:
        return reply

    return dataset.evaluate_sync(task).cases[0]


def assertions(evaluators: list, prompt: str, reply: str) -> dict[str, bool]:
    return {
        name: result.value for name, result in run(evaluators, prompt, reply).assertions.items()
    }


def test_absent_reads_off_the_cue():
    assert assertions([Slop.absent()], "explain", "let us delve in") == {"no_slop": False}
    assert assertions([Slop.absent()], "explain", "caching skips repeated work") == {
        "no_slop": True
    }


def test_expected_is_the_other_direction():
    assert assertions([Politeness.expected()], "hi", "4") == {"has_politeness": False}


def test_or_builds_a_set_that_keeps_its_members():
    result = assertions(
        [(Slop | Sycophancy | Preamble).absent()],
        "explain",
        "Great question! Certainly, let us delve in.",
    )
    assert result == {"no_slop": False, "no_sycophancy": False, "no_preamble": False}


def test_bundle_expected_checks_every_member():
    result = assertions([(Politeness | CitationMarker).expected()], "hi", "4")
    assert result == {"has_politeness": False, "has_citation_marker": False}


def test_named_bundles_are_cue_sets():
    result = assertions(
        [Servility.absent()], "explain", "Certainly! Great question, hope this helps."
    )
    assert result["no_preamble"] is False
    assert result["no_sycophancy"] is False
    assert result["no_postamble"] is False
    assert result["no_apology"] is True


def test_guards_are_keywords_on_the_verb():
    check = [Disclaimer.absent(when=NoCaveats)]
    assert assertions(
        check,
        "no disclaimers please, is it enforceable",
        "Yes, but consult a professional.",
    ) == {"no_disclaimer[when no_caveats]": False}
    assert assertions(check, "is it enforceable", "Yes, but consult a professional.") == {}


def test_unless_is_the_mirror():
    check = [Disclaimer.absent(unless=AdviceDemand)]
    assert assertions(check, "what is a tort", "A civil wrong. Not legal advice.") == {
        "no_disclaimer[unless advice_demand]": False
    }
    assert assertions(check, "should i sue my landlord", "Possibly. Not legal advice.") == {}


def test_presence_can_be_guarded_too():
    check = [CitationMarker.expected(when=CitationDemand)]
    assert assertions(check, "explain it with sources", "Caching is useful.") == {
        "has_citation_marker[when citation_demand]": False
    }
    assert assertions(check, "explain caching", "Caching is useful.") == {}


def test_field_scopes_the_check():
    from pydantic import BaseModel

    class Out(BaseModel):
        title: str
        notes: str

    dataset = Dataset(name="d", cases=[Case(inputs="x")], evaluators=[Slop.absent(field="notes")])

    async def task(text: str) -> Out:
        return Out(title="let us delve in", notes="clean")

    case = dataset.evaluate_sync(task).cases[0]
    assert case.assertions["no_slop"].value is True


def test_observe_is_the_opt_in_for_labels():
    case = run([Observe([Politeness])], "hi", "thanks!")
    assert case.labels["politeness"].value == "present"
    assert case.assertions == {}


def test_multiword_phrases_that_wrap_still_match():
    assert Sycophancy.fires("you're absolutely right about that")
    assert Preamble.fires("before we dive in, some context")


def failures(evaluators: list, prompt: str, reply: str) -> dict[str, str]:
    case = run(evaluators, prompt, reply)
    result = {}
    for name, assertion in case.assertions.items():
        if not assertion.value:
            assert assertion.reason is not None
            result[name] = assertion.reason
    return result


def test_failure_names_the_matches_and_shows_them_in_context():
    reason = failures([Slop.absent()], "explain", "Let us delve into the intricate tapestry.")[
        "no_slop"
    ]
    assert "3 slop matches" in reason
    assert '"delve"' in reason
    assert "delve -> Let us delve into the intricate tapestry." in reason


def test_failure_carries_the_fix():
    reason = failures([Slop.absent()], "explain", "let us delve in")["no_slop"]
    assert reason.endswith(Slop.fix)


def test_guidance_is_the_self_contained_fix():
    # handed back on its own, the message names the concept that fired, then the remedy
    assert Slop.guidance() == f"slop: {Slop.fix}"
    assert Slop.guidance().endswith(Slop.fix)
    # a multi-word name reads as human text, not the snake_case identifier
    assert HighPriority.guidance() == f"high priority: {HighPriority.fix}"
    assert "high_priority" not in HighPriority.guidance()


def test_failure_quotes_the_request_words_that_triggered_the_rule():
    reason = failures(
        [Disclaimer.absent(when=NoCaveats)],
        "no disclaimers please",
        "Consult a professional.",
    )["no_disclaimer[when no_caveats]"]
    assert 'the request asked for no_caveats: "no disclaimers"' in reason


def test_missing_presence_lists_what_would_satisfy_it():
    reason = failures(
        [CitationMarker.expected(when=CitationDemand)],
        "explain with sources",
        "Caching is useful.",
    )["has_citation_marker[when citation_demand]"]
    assert "expected something like: according to" in reason


def test_field_is_named_in_the_failure():
    from pydantic import BaseModel

    class Out(BaseModel):
        notes: str

    dataset = Dataset(name="d", cases=[Case(inputs="x")], evaluators=[Slop.absent(field="notes")])

    async def task(text: str) -> Out:
        return Out(notes="a rich tapestry")

    case = dataset.evaluate_sync(task).cases[0]
    reason = case.assertions["no_slop"].reason
    assert reason is not None
    assert "in notes" in reason


def test_passing_assertions_carry_no_noise():
    case = run([Slop.absent()], "explain", "caching skips repeated work")
    assert case.assertions["no_slop"].reason is None
