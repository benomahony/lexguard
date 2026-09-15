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


class TestLangChain:
    def _agent(self, *replies: str, middleware: object):
        from langchain.agents import create_agent
        from langchain_core.language_models import FakeMessagesListChatModel
        from langchain_core.messages import AIMessage

        model = FakeMessagesListChatModel(responses=[AIMessage(reply) for reply in replies])
        return create_agent(model=model, tools=[], middleware=[middleware])

    def test_clean_output_passes_straight_through(self):
        pytest.importorskip("langchain")
        from langchain_core.messages import HumanMessage

        from lexguard.integrations.guardrails.langchain import lexguard_middleware

        agent = self._agent("caching skips repeated work", middleware=lexguard_middleware(Slop))
        out = agent.invoke({"messages": [HumanMessage("explain caching")]})

        assert out["messages"][-1].text == "caching skips repeated work"
        assert out.get("lexguard_retries") is None

    def test_output_retries_back_to_the_model_with_the_reason(self):
        pytest.importorskip("langchain")
        from langchain_core.messages import HumanMessage

        from lexguard.integrations.guardrails.langchain import lexguard_middleware

        agent = self._agent(
            "let us delve into the intricate tapestry",
            "caching skips repeated work",
            middleware=lexguard_middleware(Slop),
        )
        out = agent.invoke({"messages": [HumanMessage("explain caching")]})

        assert out["messages"][-1].text == "caching skips repeated work"
        assert out["lexguard_retries"] == 1
        assert any("delve" in message.text for message in out["messages"])

    def test_output_raises_once_the_retry_budget_is_spent(self):
        pytest.importorskip("langchain")
        from langchain_core.messages import HumanMessage

        from lexguard.integrations.guardrails.langchain import (
            LexguardBlockedError,
            lexguard_middleware,
        )

        agent = self._agent(
            *(["let us delve into the intricate tapestry"] * 5),
            middleware=lexguard_middleware(Slop, retries=1),
        )

        with pytest.raises(LexguardBlockedError, match="delve"):
            agent.invoke({"messages": [HumanMessage("explain caching")]})

    def test_block_lets_clean_output_through(self):
        pytest.importorskip("langchain")
        from langchain_core.messages import HumanMessage

        from lexguard.integrations.guardrails.langchain import lexguard_middleware

        agent = self._agent(
            "caching skips repeated work",
            middleware=lexguard_middleware(Slop, on_fail="block"),
        )
        out = agent.invoke({"messages": [HumanMessage("explain caching")]})

        assert out["messages"][-1].text == "caching skips repeated work"

    def test_block_rejects_the_first_bad_output(self):
        pytest.importorskip("langchain")
        from langchain_core.messages import HumanMessage

        from lexguard.integrations.guardrails.langchain import (
            LexguardBlockedError,
            lexguard_middleware,
        )

        agent = self._agent(
            "let us delve into the intricate tapestry",
            middleware=lexguard_middleware(Slop, on_fail="block"),
        )

        with pytest.raises(LexguardBlockedError, match="delve"):
            agent.invoke({"messages": [HumanMessage("explain caching")]})

    def test_input_guard_blocks_a_bad_incoming_message(self):
        pytest.importorskip("langchain")
        from langchain_core.messages import HumanMessage

        from lexguard.integrations.guardrails.langchain import (
            LexguardBlockedError,
            lexguard_middleware,
        )

        agent = self._agent(
            "caching skips repeated work",
            middleware=lexguard_middleware(Slop, on="input", on_fail="block"),
        )

        with pytest.raises(LexguardBlockedError, match="delve"):
            agent.invoke({"messages": [HumanMessage("let us delve into the tapestry")]})

    def test_input_guard_rejects_a_retry_config(self):
        pytest.importorskip("langchain")
        from lexguard.integrations.guardrails.langchain import lexguard_middleware

        with pytest.raises(AssertionError, match="input guard can't retry"):
            lexguard_middleware(Slop, on="input")

    def test_a_bundle_combines_into_one_decision(self):
        pytest.importorskip("langchain")
        from langchain_core.messages import HumanMessage

        from lexguard.integrations.guardrails.langchain import (
            LexguardBlockedError,
            lexguard_middleware,
        )

        agent = self._agent(
            "let us delve into the tapestry, but basically it is simple",
            middleware=lexguard_middleware(Bloat, on_fail="block"),
        )

        with pytest.raises(LexguardBlockedError) as caught:
            agent.invoke({"messages": [HumanMessage("explain caching")]})
        assert "slop" in str(caught.value)
        assert "padding" in str(caught.value)
