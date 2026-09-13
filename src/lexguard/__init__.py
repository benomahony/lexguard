from __future__ import annotations

from importlib import import_module

from lexguard.lexicon import Bundle as Bundle
from lexguard.lexicon import Density as Density
from lexguard.lexicon import Hits as Hits
from lexguard.lexicon import Lexicon as Lexicon
from lexguard.lexicon import Signal as Signal
from lexguard.lexicon import Source as Source
from lexguard.lexicon import Verdict as Verdict
from lexguard.suites import Bloat as Bloat
from lexguard.suites import Leakage as Leakage
from lexguard.suites import Overreach as Overreach
from lexguard.suites import Servility as Servility
from lexguard.words import GROUPS as GROUPS
from lexguard.words import LEXICONS as LEXICONS

# spelled out explicitly (rather than `from .words.<module> import *`) so Pyright and other LSPs
# treat lexguard itself as the canonical import location for every lexicon — "add import"
# quick-fixes then suggest `from lexguard import X` instead of reaching past it into
# `lexguard.words.<module>`. PROSE/ADHERENCE/GENERIC are deliberately not re-exported here: they
# are lazy-loaded through __getattr__ below, and importing pydantic-evals is what they exist to
# defer.
from lexguard.words.demand import AdviceDemand as AdviceDemand
from lexguard.words.demand import CitationDemand as CitationDemand
from lexguard.words.demand import ComparisonDemand as ComparisonDemand
from lexguard.words.demand import CreativeDemand as CreativeDemand
from lexguard.words.demand import FactualDemand as FactualDemand
from lexguard.words.demand import OpinionDemand as OpinionDemand
from lexguard.words.demand import Revision as Revision
from lexguard.words.demand import RolePlay as RolePlay
from lexguard.words.epistemics import CitationMarker as CitationMarker
from lexguard.words.epistemics import Disclaimer as Disclaimer
from lexguard.words.epistemics import Hedging as Hedging
from lexguard.words.epistemics import Overclaim as Overclaim
from lexguard.words.epistemics import UncertaintyAdmission as UncertaintyAdmission
from lexguard.words.epistemics import UnsourcedAuthority as UnsourcedAuthority
from lexguard.words.epistemics import UnverifiedClaim as UnverifiedClaim
from lexguard.words.intent import Attachment as Attachment
from lexguard.words.intent import Confirmation as Confirmation
from lexguard.words.intent import Correction as Correction
from lexguard.words.intent import Exception as Exception
from lexguard.words.intent import Hypothetical as Hypothetical
from lexguard.words.intent import Negation as Negation
from lexguard.words.intent import Placeholder as Placeholder
from lexguard.words.intent import PriorReference as PriorReference
from lexguard.words.intent import Question as Question
from lexguard.words.intent import Vague as Vague
from lexguard.words.manner import Anthropomorphic as Anthropomorphic
from lexguard.words.manner import Apology as Apology
from lexguard.words.manner import Frustration as Frustration
from lexguard.words.manner import Politeness as Politeness
from lexguard.words.manner import Rudeness as Rudeness
from lexguard.words.manner import SelfReference as SelfReference
from lexguard.words.manner import Sycophancy as Sycophancy
from lexguard.words.priority import Effort as Effort
from lexguard.words.priority import EnergyContext as EnergyContext
from lexguard.words.priority import HighPriority as HighPriority
from lexguard.words.priority import LowPriority as LowPriority
from lexguard.words.progress import Rejection as Rejection
from lexguard.words.progress import ScopeCreep as ScopeCreep
from lexguard.words.progress import Stuck as Stuck
from lexguard.words.safety import Confidential as Confidential
from lexguard.words.safety import Injection as Injection
from lexguard.words.safety import Refusal as Refusal
from lexguard.words.safety import SystemLeak as SystemLeak
from lexguard.words.shape import FormatCode as FormatCode
from lexguard.words.shape import FormatList as FormatList
from lexguard.words.shape import FormatProse as FormatProse
from lexguard.words.shape import FormatTable as FormatTable
from lexguard.words.shape import LengthLong as LengthLong
from lexguard.words.shape import LengthShort as LengthShort
from lexguard.words.shape import NoCaveats as NoCaveats
from lexguard.words.shape import NoPreamble as NoPreamble
from lexguard.words.shape import StepByStep as StepByStep
from lexguard.words.shape import ToneCasual as ToneCasual
from lexguard.words.shape import ToneFormal as ToneFormal
from lexguard.words.style import ContrastCliche as ContrastCliche
from lexguard.words.style import EmptyIntensifier as EmptyIntensifier
from lexguard.words.style import EngagementBait as EngagementBait
from lexguard.words.style import Padding as Padding
from lexguard.words.style import Postamble as Postamble
from lexguard.words.style import Preamble as Preamble
from lexguard.words.style import Slop as Slop
from lexguard.words.style import TransitionSlop as TransitionSlop
from lexguard.words.task import Actionable as Actionable
from lexguard.words.task import Cancellation as Cancellation
from lexguard.words.task import Completion as Completion
from lexguard.words.task import Continuation as Continuation
from lexguard.words.task import Delegation as Delegation
from lexguard.words.task import Dependency as Dependency
from lexguard.words.task import Quantity as Quantity
from lexguard.words.task import SelfAssigned as SelfAssigned
from lexguard.words.task import Shared as Shared
from lexguard.words.task import Subtasks as Subtasks
from lexguard.words.time import Approximation as Approximation
from lexguard.words.time import ClockTime as ClockTime
from lexguard.words.time import ConditionalTrigger as ConditionalTrigger
from lexguard.words.time import DueDate as DueDate
from lexguard.words.time import Duration as Duration
from lexguard.words.time import EventRelative as EventRelative
from lexguard.words.time import HardDeadline as HardDeadline
from lexguard.words.time import Past as Past
from lexguard.words.time import Recurrence as Recurrence
from lexguard.words.time import SoftDeadline as SoftDeadline
from lexguard.words.topic import Children as Children
from lexguard.words.topic import Communication as Communication
from lexguard.words.topic import Garden as Garden
from lexguard.words.topic import HealthAppointment as HealthAppointment
from lexguard.words.topic import Household as Household
from lexguard.words.topic import Location as Location
from lexguard.words.topic import Maintenance as Maintenance
from lexguard.words.topic import Media as Media
from lexguard.words.topic import Money as Money
from lexguard.words.topic import Occasion as Occasion
from lexguard.words.topic import People as People
from lexguard.words.topic import Pets as Pets
from lexguard.words.topic import Shopping as Shopping
from lexguard.words.topic import Travel as Travel
from lexguard.words.topic import Work as Work

__version__ = "0.1.17"

# the shipped suites are pydantic-evals evaluator lists; deferred so importing lexguard never
# requires pydantic-evals until one is touched. the evaluators themselves live in
# lexguard.integrations.evals.pydantic_evals, not at the top level.
_SUITES = ("PROSE", "ADHERENCE", "GENERIC")


def __getattr__(name: str) -> object:
    assert name, "attribute name must not be empty"
    if name not in _SUITES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    try:
        result = vars(import_module(".suites", __name__))["__getattr__"](name)
    except ImportError as err:
        raise ImportError(
            f"lexguard.{name} needs pydantic-evals: pip install 'lexguard[pydantic-evals]'"
        ) from err
    assert result, f"lexguard.{name} is a suite, never empty"
    return result
