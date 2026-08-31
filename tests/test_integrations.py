from __future__ import annotations

import pytest

from lexguard import Check, Disclaimer, NoCaveats, Politeness, Slop, Verdict
from lexguard.words.response import Slop as SlopLexicon

pytestmark = pytest.mark.unit


def test_check_runs_with_no_framework_at_all():
    verdicts = Check([Slop]).run("let us delve in", "explain")
    assert verdicts == [Verdict(name="no_slop", passed=False, reason=verdicts[0].reason)]
    assert "delve" in verdicts[0].reason


def test_check_passes_on_clean_text():
    verdicts = Check([Slop]).run("caching skips repeated work", "explain")
    assert verdicts == [Verdict(name="no_slop", passed=True)]


def test_check_wanted_true_is_expected():
    verdicts = Check([Politeness], wanted=True).run("4", "hi")
    assert verdicts is not None
    assert verdicts[0].passed is False


def test_check_guard_skips_return_none():
    check = Check([Disclaimer], when=NoCaveats)
    assert check.run("Yes, but consult a professional.", "is it enforceable") is None


def test_check_bundle_reports_each_member():
    from lexguard import Preamble, Sycophancy

    bundle = Check([Slop, Sycophancy, Preamble])
    verdicts = bundle.run("Great question! Certainly, let us delve in.", "explain")
    assert {v.name: v.passed for v in verdicts} == {
        "no_slop": False,
        "no_sycophancy": False,
        "no_preamble": False,
    }


def test_check_needs_at_least_one_lexicon():
    with pytest.raises(AssertionError):
        Check(lexicons=[])


def test_check_rejects_both_guards():
    with pytest.raises(AssertionError):
        Check(lexicons=[SlopLexicon], when=NoCaveats, unless=NoCaveats)


def test_verdict_failing_needs_a_reason():
    with pytest.raises(AssertionError):
        Verdict(name="no_slop", passed=False)


class TestDeepEval:
    def test_metric_fails_on_slop(self):
        deepeval = pytest.importorskip("deepeval")
        from deepeval.test_case import LLMTestCase

        from lexguard.integrations.deepeval import LexguardMetric

        assert deepeval
        metric = LexguardMetric(Check([Slop]))
        test_case = LLMTestCase(input="explain caching", actual_output="let us delve in")
        score = metric.measure(test_case)
        assert score == 0.0
        assert metric.is_successful() is False
        assert "delve" in metric.reason

    def test_metric_passes_on_clean_output(self):
        pytest.importorskip("deepeval")
        from deepeval.test_case import LLMTestCase

        from lexguard.integrations.deepeval import LexguardMetric

        metric = LexguardMetric(Check([Slop]))
        test_case = LLMTestCase(
            input="explain caching", actual_output="caching skips repeated work"
        )
        score = metric.measure(test_case)
        assert score == 1.0
        assert metric.is_successful() is True
        assert metric.reason is None

    def test_metric_skips_when_guard_does_not_fire(self):
        pytest.importorskip("deepeval")
        from deepeval.test_case import LLMTestCase

        from lexguard.integrations.deepeval import LexguardMetric

        metric = LexguardMetric(Check([Disclaimer], when=NoCaveats))
        test_case = LLMTestCase(input="is it enforceable", actual_output="Consult a professional.")
        score = metric.measure(test_case)
        assert score == 1.0
        assert metric.is_successful() is True

    def test_metric_name_matches_rule_naming(self):
        pytest.importorskip("deepeval")
        from lexguard.integrations.deepeval import LexguardMetric

        assert LexguardMetric(Check([Slop])).__name__ == "no_slop"
        assert LexguardMetric(Check([Politeness], wanted=True)).__name__ == "has_politeness"

    def test_a_measure_delegates_to_measure(self):
        pytest.importorskip("deepeval")
        import asyncio

        from deepeval.test_case import LLMTestCase

        from lexguard.integrations.deepeval import LexguardMetric

        metric = LexguardMetric(Check([Slop]))
        test_case = LLMTestCase(input="explain caching", actual_output="let us delve in")
        score = asyncio.run(metric.a_measure(test_case))
        assert score == 0.0


class TestInspectAI:
    def _state(self, output_text: str, input_text: str):
        from inspect_ai.model import ChatMessageUser, ModelOutput
        from inspect_ai.solver import TaskState

        return TaskState(
            model="mockllm/model",
            sample_id=0,
            epoch=0,
            input=input_text,
            messages=[ChatMessageUser(content=input_text)],
            output=ModelOutput.from_content(model="mockllm", content=output_text),
        )

    def test_scorer_flags_slop(self):
        inspect_ai = pytest.importorskip("inspect_ai")
        import asyncio

        from inspect_ai.scorer import CORRECT, INCORRECT, Target

        from lexguard.integrations.inspect_ai import lexguard_scorer

        assert inspect_ai
        state = self._state("let us delve in", "explain caching")
        result = asyncio.run(lexguard_scorer(Check([Slop]))(state, Target("")))
        assert result.value == INCORRECT
        assert "delve" in result.explanation

        clean_state = self._state("caching skips repeated work", "explain caching")
        clean_result = asyncio.run(lexguard_scorer(Check([Slop]))(clean_state, Target("")))
        assert clean_result.value == CORRECT

    def test_scorer_skips_when_guard_does_not_fire(self):
        pytest.importorskip("inspect_ai")
        import asyncio

        from inspect_ai.scorer import CORRECT, Target

        from lexguard.integrations.inspect_ai import lexguard_scorer

        state = self._state("Consult a professional.", "is it enforceable")
        result = asyncio.run(
            lexguard_scorer(Check([Disclaimer], when=NoCaveats))(state, Target(""))
        )
        assert result.value == CORRECT
        assert result.explanation == "rule did not apply"
