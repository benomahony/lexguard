from __future__ import annotations

import pytest

from lexguard import Disclaimer, NoCaveats, Politeness, RuleSpec, Slop, Verdict
from lexguard.words.response import Slop as SlopLexicon

pytestmark = pytest.mark.unit


def test_spec_runs_with_no_framework_at_all():
    verdicts = Slop.spec().check("let us delve in", "explain")
    assert verdicts == [Verdict(name="no_slop", passed=False, reason=verdicts[0].reason)]
    assert "delve" in verdicts[0].reason


def test_spec_passes_on_clean_text():
    verdicts = Slop.spec().check("caching skips repeated work", "explain")
    assert verdicts == [Verdict(name="no_slop", passed=True)]


def test_spec_wanted_true_is_expected():
    verdicts = Politeness.spec(wanted=True).check("4", "hi")
    assert verdicts is not None
    assert verdicts[0].passed is False


def test_spec_guard_skips_return_none():
    spec = Disclaimer.spec(when=NoCaveats)
    assert spec.check("Yes, but consult a professional.", "is it enforceable") is None


def test_spec_bundle_reports_each_member():
    from lexguard import Preamble, Sycophancy

    verdicts = (
        (Slop | Sycophancy | Preamble)
        .spec()
        .check("Great question! Certainly, let us delve in.", "explain")
    )
    assert {v.name: v.passed for v in verdicts} == {
        "no_slop": False,
        "no_sycophancy": False,
        "no_preamble": False,
    }


def test_rulespec_needs_at_least_one_lexicon():
    with pytest.raises(AssertionError):
        RuleSpec(lexicons=[])


def test_rulespec_rejects_both_guards():
    with pytest.raises(AssertionError):
        RuleSpec(lexicons=[SlopLexicon], when=NoCaveats, unless=NoCaveats)


def test_verdict_failing_needs_a_reason():
    with pytest.raises(AssertionError):
        Verdict(name="no_slop", passed=False)


class TestDeepEval:
    def test_metric_fails_on_slop(self):
        deepeval = pytest.importorskip("deepeval")
        from deepeval.test_case import LLMTestCase

        from lexguard.integrations.deepeval import LexguardMetric

        assert deepeval
        metric = LexguardMetric(Slop.spec())
        test_case = LLMTestCase(input="explain caching", actual_output="let us delve in")
        score = metric.measure(test_case)
        assert score == 0.0
        assert metric.is_successful() is False
        assert "delve" in metric.reason

    def test_metric_passes_on_clean_output(self):
        pytest.importorskip("deepeval")
        from deepeval.test_case import LLMTestCase

        from lexguard.integrations.deepeval import LexguardMetric

        metric = LexguardMetric(Slop.spec())
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

        metric = LexguardMetric(Disclaimer.spec(when=NoCaveats))
        test_case = LLMTestCase(input="is it enforceable", actual_output="Consult a professional.")
        score = metric.measure(test_case)
        assert score == 1.0
        assert metric.is_successful() is True

    def test_metric_name_matches_rule_naming(self):
        pytest.importorskip("deepeval")
        from lexguard.integrations.deepeval import LexguardMetric

        assert LexguardMetric(Slop.spec()).__name__ == "no_slop"
        assert LexguardMetric(Politeness.spec(wanted=True)).__name__ == "has_politeness"

    def test_a_measure_delegates_to_measure(self):
        pytest.importorskip("deepeval")
        import asyncio

        from deepeval.test_case import LLMTestCase

        from lexguard.integrations.deepeval import LexguardMetric

        metric = LexguardMetric(Slop.spec())
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
        result = asyncio.run(lexguard_scorer(Slop.spec())(state, Target("")))
        assert result.value == INCORRECT
        assert "delve" in result.explanation

        clean_state = self._state("caching skips repeated work", "explain caching")
        clean_result = asyncio.run(lexguard_scorer(Slop.spec())(clean_state, Target("")))
        assert clean_result.value == CORRECT

    def test_scorer_skips_when_guard_does_not_fire(self):
        pytest.importorskip("inspect_ai")
        import asyncio

        from inspect_ai.scorer import CORRECT, Target

        from lexguard.integrations.inspect_ai import lexguard_scorer

        state = self._state("Consult a professional.", "is it enforceable")
        result = asyncio.run(lexguard_scorer(Disclaimer.spec(when=NoCaveats))(state, Target("")))
        assert result.value == CORRECT
        assert result.explanation == "rule did not apply"
