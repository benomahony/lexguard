from __future__ import annotations

from lexguard.lexicon import Bundle
from lexguard.words import request, response

Bloat = Bundle(
    members=(
        response.Slop,
        response.TransitionSlop,
        response.EmptyIntensifier,
        response.Padding,
        response.ContrastCliche,
        response.EngagementBait,
    )
)

Servility = Bundle(
    members=(response.Preamble, response.Postamble, response.Sycophancy, response.Apology)
)

Leakage = Bundle(
    members=(response.SelfReference, response.SystemLeak, request.Injection, request.Placeholder)
)

Overreach = Bundle(members=(response.Overclaim, response.UnsourcedAuthority))


def _prose() -> list:
    # imported here, not at module top, so importing lexguard never pulls in pydantic-evals
    from lexguard.integrations.evals.pydantic_evals import LexguardEvaluator

    bundles = (Bloat, Servility, Leakage, Overreach)
    result = [LexguardEvaluator(bundle) for bundle in bundles]
    assert len(result) == len(bundles), "PROSE checks every prose-quality bundle, one rule each"
    assert all(rule is not None for rule in result), "every bundle builds its own rule"
    return result


def _adherence() -> list:
    # unconditional house-style rules only: a rule that's only right when the request asked
    # for it (e.g. "cite sources" or "admit uncertainty") needs a guard lexguard doesn't have
    # yet — see when/unless in git history if reintroducing conditional rules.
    from lexguard.integrations.evals.pydantic_evals import LexguardEvaluator

    # Overclaim is already covered unconditionally by PROSE's Overreach bundle; not repeated here
    result = [
        LexguardEvaluator(response.Disclaimer),
        LexguardEvaluator(response.Hedging),
        LexguardEvaluator(response.Anthropomorphic),
    ]
    assert len(result) == 3, "ADHERENCE is the three unconditional instruction-following rules"
    assert all(rule is not None for rule in result), "every entry builds a rule"
    return result


def __getattr__(name: str) -> list:
    # deferred so importing lexguard never requires pydantic-evals until these are touched
    assert name, "attribute name must not be empty"
    if name == "PROSE":
        return _prose()
    if name == "ADHERENCE":
        return _adherence()
    if name == "GENERIC":
        result = [*_prose(), *_adherence()]
        assert result, "GENERIC combines the prose and adherence suites into a non-empty list"
        return result
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
