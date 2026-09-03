from __future__ import annotations

import pytest
from pydantic_evals import Case, Dataset

from lexguard import Confirmation, Politeness
from lexguard.integrations.evals.pydantic_evals import LexguardEvaluator, Observe
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
    assert assertions([LexguardEvaluator(Slop)], "explain", "let us delve in") == {"Slop": False}
    assert assertions([LexguardEvaluator(Slop)], "explain", "caching skips repeated work") == {
        "Slop": True
    }


def test_fail_when_neutral_requires_an_actual_match():
    assert assertions([LexguardEvaluator(Confirmation)], "confirm?", "maybe, not sure yet") == {
        "Confirmation": False
    }
    assert assertions([LexguardEvaluator(Confirmation)], "confirm?", "yes, confirmed") == {
        "Confirmation": True
    }


def test_observe_is_the_opt_in_for_labels():
    case = run([Observe(Politeness)], "hi", "thanks!")
    assert case.labels["Politeness"].value == "present"
    assert case.assertions == {}


def test_multiword_phrases_that_wrap_still_match():
    from lexguard import Preamble, Sycophancy

    assert Sycophancy.matches("you're absolutely right about that")
    assert Preamble.matches("before we dive in, some context")


def failures(evaluators: list, prompt: str, reply: str) -> dict[str, str]:
    case = run(evaluators, prompt, reply)
    result = {}
    for name, assertion in case.assertions.items():
        if not assertion.value:
            assert assertion.reason is not None
            result[name] = assertion.reason
    return result


def test_failure_names_the_matches_and_shows_them_in_context():
    reason = failures(
        [LexguardEvaluator(Slop)], "explain", "Let us delve into the intricate tapestry."
    )["Slop"]
    assert "3 slop matches" in reason
    assert '"delve"' in reason
    assert "delve -> Let us delve into the intricate tapestry." in reason


def test_failure_carries_the_fix():
    reason = failures([LexguardEvaluator(Slop)], "explain", "let us delve in")["Slop"]
    assert reason.endswith(Slop.fix)


def test_fail_when_neutral_failure_lists_what_would_satisfy_it():
    reason = failures([LexguardEvaluator(Confirmation)], "confirm?", "maybe, not sure yet")[
        "Confirmation"
    ]
    assert "expected something like" in reason
    assert reason.endswith(Confirmation.fix)


def test_passing_assertions_carry_no_noise():
    case = run([LexguardEvaluator(Slop)], "explain", "caching skips repeated work")
    assert case.assertions["Slop"].reason is None


def test_denied_fail_when_neutral_names_the_blocker():
    reason = Politeness.verdict("could you please fix the fucking bug").reason
    assert reason is not None
    assert 'denied by: "fucking"' in reason
    assert reason.endswith(Politeness.fix)


def test_evaluator_labels_split_indicated_from_ruled_out():
    case = run(
        [LexguardEvaluator(Politeness)], "fix the bug", "could you please fix the fucking bug"
    )
    assert case.labels["PolitenessIndicated"].value == "could you, please"
    assert case.labels["PolitenessRuledOut"].value == "fucking"


def test_evaluator_scores_a_real_density_not_a_raw_count():
    reply = "could you please fix the fucking bug"
    case = run([LexguardEvaluator(Politeness)], "fix the bug", reply)
    density = Politeness.density(reply)
    assert case.scores["PolitenessIndicatedDensity"].value == density.indicated
    assert case.scores["PolitenessRuledOutDensity"].value == density.ruled_out

    clean = run([LexguardEvaluator(Slop)], "explain", "caching skips repeated work")
    assert clean.scores["SlopIndicatedDensity"].value == 0.0
    assert "SlopRuledOutDensity" not in clean.scores


def test_evaluator_omits_hit_labels_when_nothing_matched():
    case = run([LexguardEvaluator(Slop)], "explain", "caching skips repeated work")
    assert "SlopIndicated" not in case.labels
    assert "SlopRuledOut" not in case.labels
