from __future__ import annotations

from .lexicon import Bundle
from .words import instruction as ask
from .words import request as req
from .words import response as out

Bloat = Bundle(
    members=(
        out.Slop,
        out.TransitionSlop,
        out.EmptyIntensifier,
        out.Padding,
        out.ContrastCliche,
        out.EngagementBait,
    )
)

Servility = Bundle(members=(out.Preamble, out.Postamble, out.Sycophancy, out.Apology))

Leakage = Bundle(members=(out.SelfReference, out.SystemLeak, req.Injection, req.Placeholder))

Overreach = Bundle(members=(out.Overclaim, out.UnsourcedAuthority))


def _prose() -> list:
    result = [Bloat.absent(), Servility.absent(), Leakage.absent(), Overreach.absent()]
    assert len(result) == 4
    assert all(rule is not None for rule in result)
    return result


def _adherence() -> list:
    result = [
        out.Disclaimer.absent(unless=ask.AdviceDemand),
        out.Hedging.absent(when=ask.NoCaveats),
        Servility.absent(when=ask.NoPreamble),
        out.Anthropomorphic.absent(unless=ask.RolePlay),
        out.Overclaim.absent(unless=ask.CreativeDemand),
        out.CitationMarker.expected(when=ask.CitationDemand),
        out.UncertaintyAdmission.expected(when=ask.FactualDemand),
    ]
    assert len(result) == 7
    assert all(rule is not None for rule in result)
    return result


def __getattr__(name: str) -> list:
    # deferred so importing lexguard never requires pydantic-evals until these are touched
    assert isinstance(name, str)
    assert name, "attribute name must not be empty"
    if name == "PROSE":
        return _prose()
    if name == "ADHERENCE":
        return _adherence()
    if name == "GENERIC":
        return [*_prose(), *_adherence()]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
