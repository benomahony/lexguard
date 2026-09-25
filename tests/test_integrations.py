from __future__ import annotations

import pytest

from lexguard import Density, Politeness, Verdict
from lexguard.suites import Bloat
from lexguard.words.style import Slop

pytestmark = pytest.mark.unit


def test_verdict_failing_needs_a_reason():
    with pytest.raises(AssertionError):
        Verdict(passed=False)


def test_density_rejects_values_outside_zero_to_one():
    with pytest.raises(AssertionError):
        Density(indicated=1.5, ruled_out=0.0)
    with pytest.raises(AssertionError):
        Density(indicated=0.0, ruled_out=-0.1)


class TestDeepEval:
    def test_metric_fails_on_slop(self):
        deepeval = pytest.importorskip("deepeval")
        from deepeval.test_case import LLMTestCase

        from lexguard.integrations.evals.deepeval import LexguardMetric

        assert deepeval
        metric = LexguardMetric(Slop)
        test_case = LLMTestCase(input="explain caching", actual_output="let us delve in")
        score = metric.measure(test_case)
        assert score == 0.0
        assert metric.is_successful() is False
        assert "delve" in metric.reason

    def test_metric_passes_on_clean_output(self):
        pytest.importorskip("deepeval")
        from deepeval.test_case import LLMTestCase

        from lexguard.integrations.evals.deepeval import LexguardMetric

        metric = LexguardMetric(Slop)
        test_case = LLMTestCase(
            input="explain caching", actual_output="caching skips repeated work"
        )
        score = metric.measure(test_case)
        assert score == 1.0
        assert metric.is_successful() is True
        assert metric.reason is None

    def test_metric_breakdown_is_a_density_not_a_raw_count(self):
        pytest.importorskip("deepeval")
        from deepeval.test_case import LLMTestCase

        from lexguard.integrations.evals.deepeval import LexguardMetric

        metric = LexguardMetric(Politeness)
        test_case = LLMTestCase(
            input="fix the bug", actual_output="could you please fix the fucking bug"
        )
        metric.measure(test_case)
        assert metric.score_breakdown == Politeness.density(str(test_case.actual_output)).__dict__

        once = LLMTestCase(input="fix the bug", actual_output="fucking fix the bug now please")
        metric.measure(once)
        once_density = metric.score_breakdown["ruled_out"]

        repeated = LLMTestCase(
            input="fix the bug", actual_output="fucking fucking fucking fix the bug now please"
        )
        metric.measure(repeated)
        assert metric.score_breakdown["ruled_out"] > once_density

    def test_metric_breakdown_omits_ruled_out_for_a_lexicon_without_one(self):
        pytest.importorskip("deepeval")
        from deepeval.test_case import LLMTestCase

        from lexguard.integrations.evals.deepeval import LexguardMetric

        assert Slop.rules_out == frozenset()
        metric = LexguardMetric(Slop)
        test_case = LLMTestCase(input="explain caching", actual_output="let us delve in")
        metric.measure(test_case)
        assert "ruled_out" not in metric.score_breakdown

    def test_metric_name_matches_rule_naming(self):
        pytest.importorskip("deepeval")
        from lexguard.integrations.evals.deepeval import LexguardMetric

        assert LexguardMetric(Slop).__name__ == "Slop"
        assert LexguardMetric(Politeness).__name__ == "Politeness"

    def test_a_measure_delegates_to_measure(self):
        pytest.importorskip("deepeval")
        import asyncio

        from deepeval.test_case import LLMTestCase

        from lexguard.integrations.evals.deepeval import LexguardMetric

        metric = LexguardMetric(Slop)
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

        from lexguard.integrations.evals.inspect_ai import lexguard_scorer

        assert inspect_ai
        state = self._state("let us delve in", "explain caching")
        result = asyncio.run(lexguard_scorer(Slop)(state, Target("")))
        assert result.value == INCORRECT
        assert "delve" in result.explanation

        clean_state = self._state("caching skips repeated work", "explain caching")
        clean_result = asyncio.run(lexguard_scorer(Slop)(clean_state, Target("")))
        assert clean_result.value == CORRECT

    def test_scorer_metadata_is_a_density_not_a_raw_count(self):
        pytest.importorskip("inspect_ai")
        import asyncio

        from inspect_ai.scorer import Target

        from lexguard.integrations.evals.inspect_ai import lexguard_scorer

        text = "could you please fix the fucking bug"
        state = self._state(text, "fix the bug")
        result = asyncio.run(lexguard_scorer(Politeness)(state, Target("")))
        assert result.metadata == Politeness.density(text).__dict__

    def test_scorer_metadata_omits_ruled_out_for_a_lexicon_without_one(self):
        pytest.importorskip("inspect_ai")
        import asyncio

        from inspect_ai.scorer import Target

        from lexguard.integrations.evals.inspect_ai import lexguard_scorer

        assert Slop.rules_out == frozenset()
        state = self._state("let us delve in", "explain caching")
        result = asyncio.run(lexguard_scorer(Slop)(state, Target("")))
        assert "ruled_out" not in result.metadata

    def test_scorers_are_named_for_their_lexicons(self, tmp_path):
        pytest.importorskip("inspect_ai")
        from inspect_ai import Task, eval
        from inspect_ai.dataset import Sample
        from inspect_ai.solver import generate

        from lexguard.integrations.evals.inspect_ai import lexguard_scorer

        task = Task(
            dataset=[Sample(input="explain caching")],
            solver=generate(),
            scorer=[lexguard_scorer(Slop), lexguard_scorer(Politeness)],
        )
        log = eval(task, model="mockllm/model", display="none", log_dir=str(tmp_path))[0]
        assert log.results is not None
        # not Inspect's default closure name with a numeric suffix per duplicate
        assert [score.name for score in log.results.scores] == ["Slop", "Politeness"]


class TestGuardrails:
    def test_guard_allows_clean_text(self):
        pytest.importorskip("pydantic_ai_harness")
        from lexguard.integrations.guardrails.pydantic_ai import lexguard_guard

        guard = lexguard_guard(Slop)
        result = guard("caching skips repeated work")

        assert result.action == "allow"
        assert result.message is None

    def test_guard_retries_on_a_single_lexicon_by_default(self):
        pytest.importorskip("pydantic_ai_harness")
        from lexguard.integrations.guardrails.pydantic_ai import lexguard_guard

        guard = lexguard_guard(Slop)
        result = guard("let us delve into the intricate tapestry")

        assert result.action == "retry"
        assert result.message is not None
        assert "delve" in result.message

    def test_guard_can_block_on_a_single_lexicon(self):
        pytest.importorskip("pydantic_ai_harness")
        from lexguard.integrations.guardrails.pydantic_ai import lexguard_guard

        guard = lexguard_guard(Slop, on_fail="block")
        result = guard("let us delve into the intricate tapestry")

        assert result.action == "block"
        assert result.message is not None
        assert "delve" in result.message

    def test_guard_over_a_bundle_combines_into_one_decision(self):
        pytest.importorskip("pydantic_ai_harness")
        from lexguard.integrations.guardrails.pydantic_ai import lexguard_guard

        guard = lexguard_guard(Bloat)
        assert guard("caching skips repeated work").action == "allow"

        result = guard("let us delve into the intricate tapestry, but basically it is simple")

        assert result.action == "retry"
        assert result.message is not None
        assert "slop" in result.message
        assert "padding" in result.message

    def test_retry_works_as_a_real_output_guardrail(self):
        pytest.importorskip("pydantic_ai_harness")
        from pydantic_ai import Agent, UnexpectedModelBehavior
        from pydantic_ai.models.test import TestModel
        from pydantic_ai_harness.guardrails import OutputGuardrail

        from lexguard.integrations.guardrails.pydantic_ai import lexguard_guard

        agent = Agent(
            TestModel(custom_output_text="let us delve into the intricate tapestry"),
            capabilities=[OutputGuardrail(guard=lexguard_guard(Slop))],
        )

        with pytest.raises(UnexpectedModelBehavior):
            agent.run_sync("explain caching")

    def test_block_works_as_a_real_output_guardrail(self):
        pytest.importorskip("pydantic_ai_harness")
        from pydantic_ai import Agent
        from pydantic_ai.models.test import TestModel
        from pydantic_ai_harness.guardrails import OutputBlocked, OutputGuardrail

        from lexguard.integrations.guardrails.pydantic_ai import lexguard_guard

        agent = Agent(
            TestModel(custom_output_text="let us delve into the intricate tapestry"),
            capabilities=[
                OutputGuardrail(
                    guard=lexguard_guard(Slop, on_fail="block"),
                )
            ],
        )

        with pytest.raises(OutputBlocked):
            agent.run_sync("explain caching")


class TestDynamicLexguard:
    def test_an_agent_created_lexguard_checks_the_same_run(self):
        pytest.importorskip("pydantic_ai_harness")
        from pydantic_ai import Agent
        from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart
        from pydantic_ai.models.function import AgentInfo, FunctionModel

        from lexguard.integrations.guardrails.pydantic_ai import DynamicLexguard

        def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
            match len(messages):
                case 1:
                    ban = {"name": "banned", "indicates": ["cache"], "fix": "say store"}
                    return ModelResponse(parts=[ToolCallPart("update_lexguard", ban)])
                case 3:
                    return ModelResponse(parts=[TextPart("the cache helps")])
                case _:
                    return ModelResponse(parts=[TextPart("the store helps")])

        capability = DynamicLexguard(Slop)
        result = Agent(FunctionModel(model), capabilities=[capability]).run_sync("explain")

        assert result.output == "the store helps"
        assert set(capability.lexicons) == {"slop", "banned"}

    def test_update_edits_terms_in_place(self):
        pytest.importorskip("pydantic_ai_harness")
        from lexguard.integrations.guardrails.pydantic_ai import DynamicLexguard

        capability = DynamicLexguard(Slop)
        capability.update_lexguard("slop", indicates=["Synergy"], remove=["delve"])

        assert "synergy" in capability.lexicons["slop"].indicates
        assert "delve" not in capability.lexicons["slop"].indicates
        assert capability.lexicons["slop"].fix == Slop.fix
        assert capability.check("let us delve").action == "allow"
        assert capability.check("pure synergy").action == "retry"

    def test_update_moves_a_term_between_lists(self):
        pytest.importorskip("pydantic_ai_harness")
        from lexguard.integrations.guardrails.pydantic_ai import DynamicLexguard

        capability = DynamicLexguard()
        capability.update_lexguard("banned", indicates=["cache"], fix="say store")
        capability.update_lexguard("banned", rules_out=["cache"])

        assert capability.lexicons["banned"].rules_out == frozenset({"cache"})
        assert capability.lexicons["banned"].indicates == frozenset()

    def test_update_refuses_bad_edits(self):
        pytest.importorskip("pydantic_ai_harness")
        from pydantic_ai.exceptions import ModelRetry

        from lexguard.integrations.guardrails.pydantic_ai import DynamicLexguard

        capability = DynamicLexguard()
        with pytest.raises(ModelRetry, match="pass a `fix`"):
            capability.update_lexguard("banned", indicates=["cache"])
        with pytest.raises(ModelRetry, match="both indicate and rule out"):
            capability.update_lexguard("banned", indicates=["x"], rules_out=["X"], fix="no")

    def test_list_and_remove(self):
        pytest.importorskip("pydantic_ai_harness")
        from lexguard.integrations.guardrails.pydantic_ai import DynamicLexguard

        capability = DynamicLexguard(Bloat)
        assert "Lexicon(name='padding'" in capability.list_lexguards()

        assert capability.remove_lexguard("padding") == "removed padding"
        assert capability.remove_lexguard("padding") == "No lexguard named 'padding'."
        capability.lexicons.clear()
        assert capability.list_lexguards() == "No lexguards are active."
        assert capability.check("let us delve").action == "allow"
