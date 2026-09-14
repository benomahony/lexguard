from __future__ import annotations

from lexguard.lexicon import Bundle
from lexguard.words import epistemics, intent, progress, safety, style, tone

Bloat = Bundle(
    members=(
        style.Slop,
        style.TransitionSlop,
        style.EmptyIntensifier,
        style.Padding,
        style.ContrastCliche,
        style.EngagementBait,
    )
)

Servility = Bundle(members=(style.Preamble, style.Postamble, tone.Sycophancy, tone.Apology))

Leakage = Bundle(
    members=(tone.SelfReference, safety.SystemLeak, safety.Injection, intent.Placeholder)
)

Overreach = Bundle(members=(epistemics.Overclaim, epistemics.UnsourcedAuthority))

# signs an agent session is going badly: the user pushing back or exasperated, the agent stalled,
# overstepping, or claiming success it has not shown. speaker-agnostic, so aim each member at the
# turn you care about.
Trouble = Bundle(
    members=(
        progress.Rejection,
        progress.Stuck,
        progress.ScopeCreep,
        tone.Frustration,
        epistemics.UnverifiedClaim,
    )
)


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
        LexguardEvaluator(epistemics.Disclaimer),
        LexguardEvaluator(epistemics.Hedging),
        LexguardEvaluator(tone.Anthropomorphic),
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
