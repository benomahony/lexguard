from __future__ import annotations

from importlib import import_module

from lexguard.lexicon import Bundle as Bundle
from lexguard.lexicon import Density as Density
from lexguard.lexicon import Hits as Hits
from lexguard.lexicon import Lexicon as Lexicon
from lexguard.lexicon import Signal as Signal
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
from lexguard.words.domain import Children as Children
from lexguard.words.domain import Communication as Communication
from lexguard.words.domain import Garden as Garden
from lexguard.words.domain import HealthAppointment as HealthAppointment
from lexguard.words.domain import Household as Household
from lexguard.words.domain import Location as Location
from lexguard.words.domain import Maintenance as Maintenance
from lexguard.words.domain import Media as Media
from lexguard.words.domain import Money as Money
from lexguard.words.domain import Occasion as Occasion
from lexguard.words.domain import People as People
from lexguard.words.domain import Pets as Pets
from lexguard.words.domain import Shopping as Shopping
from lexguard.words.domain import Travel as Travel
from lexguard.words.domain import Work as Work
from lexguard.words.instruction import AdviceDemand as AdviceDemand
from lexguard.words.instruction import CitationDemand as CitationDemand
from lexguard.words.instruction import ComparisonDemand as ComparisonDemand
from lexguard.words.instruction import CreativeDemand as CreativeDemand
from lexguard.words.instruction import FactualDemand as FactualDemand
from lexguard.words.instruction import FormatCode as FormatCode
from lexguard.words.instruction import FormatList as FormatList
from lexguard.words.instruction import FormatProse as FormatProse
from lexguard.words.instruction import FormatTable as FormatTable
from lexguard.words.instruction import LengthLong as LengthLong
from lexguard.words.instruction import LengthShort as LengthShort
from lexguard.words.instruction import NoCaveats as NoCaveats
from lexguard.words.instruction import NoPreamble as NoPreamble
from lexguard.words.instruction import OpinionDemand as OpinionDemand
from lexguard.words.instruction import Revision as Revision
from lexguard.words.instruction import RolePlay as RolePlay
from lexguard.words.instruction import StepByStep as StepByStep
from lexguard.words.instruction import ToneCasual as ToneCasual
from lexguard.words.instruction import ToneFormal as ToneFormal
from lexguard.words.request import Actionable as Actionable
from lexguard.words.request import Approximation as Approximation
from lexguard.words.request import Attachment as Attachment
from lexguard.words.request import Cancellation as Cancellation
from lexguard.words.request import ClockTime as ClockTime
from lexguard.words.request import Completion as Completion
from lexguard.words.request import ConditionalTrigger as ConditionalTrigger
from lexguard.words.request import Confidential as Confidential
from lexguard.words.request import Confirmation as Confirmation
from lexguard.words.request import Continuation as Continuation
from lexguard.words.request import Correction as Correction
from lexguard.words.request import Delegation as Delegation
from lexguard.words.request import Dependency as Dependency
from lexguard.words.request import DueDate as DueDate
from lexguard.words.request import Duration as Duration
from lexguard.words.request import Effort as Effort
from lexguard.words.request import EnergyContext as EnergyContext
from lexguard.words.request import EventRelative as EventRelative
from lexguard.words.request import Exception as Exception
from lexguard.words.request import HardDeadline as HardDeadline
from lexguard.words.request import HighPriority as HighPriority
from lexguard.words.request import Hypothetical as Hypothetical
from lexguard.words.request import Injection as Injection
from lexguard.words.request import LowPriority as LowPriority
from lexguard.words.request import Negation as Negation
from lexguard.words.request import Past as Past
from lexguard.words.request import Placeholder as Placeholder
from lexguard.words.request import Politeness as Politeness
from lexguard.words.request import PriorReference as PriorReference
from lexguard.words.request import Quantity as Quantity
from lexguard.words.request import Question as Question
from lexguard.words.request import Recurrence as Recurrence
from lexguard.words.request import SelfAssigned as SelfAssigned
from lexguard.words.request import Shared as Shared
from lexguard.words.request import SoftDeadline as SoftDeadline
from lexguard.words.request import Subtasks as Subtasks
from lexguard.words.request import Vague as Vague
from lexguard.words.response import Anthropomorphic as Anthropomorphic
from lexguard.words.response import Apology as Apology
from lexguard.words.response import CitationMarker as CitationMarker
from lexguard.words.response import ContrastCliche as ContrastCliche
from lexguard.words.response import Disclaimer as Disclaimer
from lexguard.words.response import EmptyIntensifier as EmptyIntensifier
from lexguard.words.response import EngagementBait as EngagementBait
from lexguard.words.response import Hedging as Hedging
from lexguard.words.response import Overclaim as Overclaim
from lexguard.words.response import Padding as Padding
from lexguard.words.response import Postamble as Postamble
from lexguard.words.response import Preamble as Preamble
from lexguard.words.response import Refusal as Refusal
from lexguard.words.response import Rudeness as Rudeness
from lexguard.words.response import SelfReference as SelfReference
from lexguard.words.response import Slop as Slop
from lexguard.words.response import Sycophancy as Sycophancy
from lexguard.words.response import SystemLeak as SystemLeak
from lexguard.words.response import TransitionSlop as TransitionSlop
from lexguard.words.response import UncertaintyAdmission as UncertaintyAdmission
from lexguard.words.response import UnsourcedAuthority as UnsourcedAuthority

__version__ = "0.1.16"

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
