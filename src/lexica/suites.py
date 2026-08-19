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

PROSE = [Bloat.absent(), Servility.absent(), Leakage.absent(), Overreach.absent()]

ADHERENCE = [
    out.Disclaimer.absent(unless=ask.AdviceDemand),
    out.Hedging.absent(when=ask.NoCaveats),
    Servility.absent(when=ask.NoPreamble),
    out.Anthropomorphic.absent(unless=ask.RolePlay),
    out.Overclaim.absent(unless=ask.CreativeDemand),
    out.CitationMarker.expected(when=ask.CitationDemand),
    out.UncertaintyAdmission.expected(when=ask.FactualDemand),
]

GENERIC = [*PROSE, *ADHERENCE]
