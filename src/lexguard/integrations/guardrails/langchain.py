from __future__ import annotations

from typing import Any, Literal, NotRequired

from langchain.agents.middleware import (
    AgentMiddleware,
    AgentState,
    after_model,
    before_model,
)
from langchain.messages import HumanMessage

from lexguard.lexicon import Bundle, Lexicon

__all__ = ["LexguardBlockedError", "lexguard_middleware"]


class LexguardBlockedError(Exception):
    """Raised by a `lexguard_middleware` when a checked message fails and there's no retry left —
    on the first failure for `on_fail="block"`, or once the retry budget is spent. The message is
    the same lexicon diagnosis every other integration surfaces; see `Lexicon.verdict`.
    """


class _RetryState(AgentState):
    # Keyed by middleware name, so several retry guards on one agent keep separate budgets.
    lexguard_retries: NotRequired[dict[str, int]]


def _middleware_name(lexicons: tuple[Lexicon, ...], on: str, on_fail: str) -> str:
    """A deterministic name per guard, since `create_agent` rejects duplicate middleware names."""
    assert lexicons, "a guard checks at least one lexicon"
    name = f"Lexguard_{on}_{on_fail}_" + "_".join(lexicon.name for lexicon in lexicons)
    assert lexicons[0].name in name, "the name identifies what the guard checks"
    return name


def _combined_reason(lexicons: tuple[Lexicon, ...], text: str) -> str | None:
    """The joined failure reason across every lexicon, or `None` if the text passes them all."""
    verdicts = [lexicon.verdict(text) for lexicon in lexicons]
    assert len(verdicts) == len(lexicons), "one verdict per lexicon checked"
    failures = [verdict for verdict in verdicts if not verdict.passed]
    if not failures:
        return None
    reason = "\n\n".join(failure.reason or "" for failure in failures)
    assert reason, "a failure always carries a reason"
    return reason


def _block_middleware(lexicons: tuple[Lexicon, ...], on: str) -> AgentMiddleware[Any, Any, Any]:
    """A middleware that rejects the first failing message outright by raising."""
    assert lexicons, "a middleware needs at least one lexicon to check"
    assert on in ("input", "output"), "a guard runs before or after the model"

    def block_hook(state: AgentState[Any], _runtime: Any) -> None:
        messages = state["messages"]
        assert messages, "the middleware checks the last message, so there must be one"
        reason = _combined_reason(lexicons, messages[-1].text)
        if reason is None:
            return None
        assert reason, "a blocked message always carries a reason"
        raise LexguardBlockedError(reason)

    builder = before_model if on == "input" else after_model
    return builder(name=_middleware_name(lexicons, on, "block"))(block_hook)


def _retry_middleware(
    lexicons: tuple[Lexicon, ...], retries: int
) -> AgentMiddleware[Any, Any, Any]:
    """A middleware that loops a failing reply back to the model, then raises once out of budget."""
    assert lexicons, "a middleware needs at least one lexicon to check"
    assert retries >= 1, "a retry budget of at least 1 is needed to retry"
    name = _middleware_name(lexicons, "output", "retry")

    def retry_hook(state: _RetryState, _runtime: Any) -> dict[str, Any] | None:
        messages = state["messages"]
        assert messages, "the middleware checks the last message, so there must be one"
        counts = state.get("lexguard_retries", {})
        used = counts.get(name, 0)
        assert used <= retries, "the retry counter never runs past the budget"
        reason = _combined_reason(lexicons, messages[-1].text)
        if reason is None:
            if not used:
                return None
            # Reset on a pass so a checkpointed thread's later turns get the full budget again.
            return {"lexguard_retries": {**counts, name: 0}}
        if used >= retries:
            raise LexguardBlockedError(reason)
        return {
            "messages": [HumanMessage(reason)],
            "jump_to": "model",
            "lexguard_retries": {**counts, name: used + 1},
        }

    return after_model(
        state_schema=_RetryState,
        can_jump_to=["model", "end"],
        name=name,
    )(retry_hook)


def lexguard_middleware(
    target: Lexicon | Bundle,
    *,
    on: Literal["input", "output"] = "output",
    on_fail: Literal["block", "retry"] = "retry",
    retries: int = 1,
) -> AgentMiddleware[Any, Any, Any]:
    """Build a LangChain agent middleware that checks a message against a `Lexicon` (or a `Bundle`
    of them) as it flows through a `create_agent` agent. Whether each lexicon asserts presence or
    absence is its own `fail_when_neutral`; see `Lexicon.verdict`.

    Like the other guardrail adapter and unlike the eval ones, a `Bundle` here combines into a
    single decision, since a hook resolves to one action — but a failure still lists every lexicon
    that fired, so nothing is hidden.

    `on` picks the hook, mirroring pydantic-ai's input/output guardrail split:

    - `on="output"` (the default) runs `after_model` against the model's reply.
    - `on="input"` runs `before_model` against the latest incoming message.

    On a failure:

    - `on_fail="retry"` (the default, output only) hands the model the lexicon reason and loops
      back for another attempt, up to `retries` times (default 1); once the budget is spent it
      raises `LexguardBlockedError`. There's nothing to retry on the input side, so `on="input"`
      requires `on_fail="block"`.
    - `on_fail="block"` raises `LexguardBlockedError` on the first failure, rejecting the value
      outright.

    Drop it into `create_agent`::

        from langchain.agents import create_agent

        agent = create_agent(model, middleware=[lexguard_middleware(Slop)])
    """
    lexicons = target.members if isinstance(target, Bundle) else (target,)
    assert lexicons, "a middleware needs at least one lexicon to check"
    assert all(lexicon.name for lexicon in lexicons), "every lexicon has a name"
    if on == "input":
        assert on_fail == "block", "an input guard can't retry the model; use on_fail='block'"
    if on_fail == "block":
        return _block_middleware(lexicons, on)
    assert on == "output", "retry only applies to the model's own output"
    return _retry_middleware(lexicons, retries)
