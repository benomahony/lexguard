from __future__ import annotations

import pytest
from pydantic_evals import Case, Dataset

from lexguard.integrations.pydantic_evals import absent, expected
from lexguard.suites import GENERIC
from lexguard.words import instruction, response

pytestmark = pytest.mark.unit


def verdicts(evaluators: list, prompt: str, reply: str) -> dict[str, bool]:
    dataset = Dataset(name="t", cases=[Case(name="c", inputs=prompt)], evaluators=evaluators)

    async def task(text: str) -> str:
        return reply

    report = dataset.evaluate_sync(task)
    return {name: result.value for name, result in report.cases[0].assertions.items()}


def test_slop_is_caught_in_plain_output():
    result = verdicts(
        [absent(response.Slop)],
        "explain caching",
        "Let us delve into the intricate tapestry of caching.",
    )
    assert result["no_slop"] is False


def test_clean_prose_passes_the_whole_generic_suite():
    reply = (
        "Caching stores a computed result so the next request can skip the work. "
        "The cost is staleness."
    )
    failures = [
        name
        for name, passed in verdicts(GENERIC, "explain caching", reply).items()
        if passed is False
    ]
    assert failures == []


def test_no_caveats_suppresses_disclaimers():
    check = [absent(response.Disclaimer, when=instruction.NoCaveats)]
    result = verdicts(
        check,
        "no disclaimers please, is this contract enforceable",
        "It likely is, but consult a professional.",
    )
    assert result["no_disclaimer[when no_caveats]"] is False


def test_disclaimer_is_fine_when_no_suppression_asked():
    check = [absent(response.Disclaimer, when=instruction.NoCaveats)]
    result = verdicts(
        check,
        "is this contract enforceable",
        "It likely is, but consult a professional.",
    )
    assert result == {}


def test_disclaimer_gated_on_advice_being_sought():
    check = [absent(response.Disclaimer, unless=instruction.AdviceDemand)]
    assert (
        verdicts(
            check,
            "what is a tort",
            "A tort is a civil wrong. This is not legal advice.",
        )["no_disclaimer[unless advice_demand]"]
        is False
    )
    assert verdicts(check, "should i sue my landlord", "Possibly. This is not legal advice.") == {}


def test_citations_required_only_when_asked():
    check = [expected(response.CitationMarker, when=instruction.CitationDemand)]
    assert (
        verdicts(check, "explain it with sources", "Caching is useful.")[
            "has_citation_marker[when citation_demand]"
        ]
        is False
    )
    assert verdicts(check, "explain caching", "Caching is useful.") == {}


def test_no_preamble_suppresses_openers():
    check = [absent(response.Preamble, when=instruction.NoPreamble)]
    result = verdicts(
        check,
        "just give me the answer, no preamble",
        "Certainly. Here's a breakdown of the answer.",
    )
    assert result["no_preamble[when no_preamble]"] is False


def test_instruction_pairs_block_each_other():
    assert instruction.LengthShort.denied("give me a comprehensive detailed breakdown")
    assert instruction.LengthLong.denied("keep it short, one sentence")
    assert instruction.FormatProse.denied("write it as bullet points")
