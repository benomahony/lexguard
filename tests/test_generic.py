from __future__ import annotations

import pytest
from pydantic_evals import Case, Dataset

from lexguard.integrations.evals.pydantic_evals import LexguardEvaluator
from lexguard.suites import GENERIC
from lexguard.words import response

pytestmark = pytest.mark.unit


def verdicts(evaluators: list, prompt: str, reply: str) -> dict[str, bool]:
    dataset = Dataset(name="t", cases=[Case(name="c", inputs=prompt)], evaluators=evaluators)

    async def task(text: str) -> str:
        return reply

    report = dataset.evaluate_sync(task)
    return {name: result.value for name, result in report.cases[0].assertions.items()}


def test_slop_is_caught_in_plain_output():
    result = verdicts(
        [LexguardEvaluator(response.Slop)],
        "explain caching",
        "Let us delve into the intricate tapestry of caching.",
    )
    assert result["Slop"] is False


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


def test_instruction_pairs_block_each_other():
    from lexguard.words import instruction

    assert instruction.LengthShort.denied("give me a comprehensive detailed breakdown")
    assert instruction.LengthLong.denied("keep it short, one sentence")
    assert instruction.FormatProse.denied("write it as bullet points")
