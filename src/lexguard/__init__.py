from __future__ import annotations

from importlib import import_module

from .lexicon import Bundle as Bundle
from .lexicon import Lexicon as Lexicon
from .lexicon import Signal as Signal
from .rulespec import ObserveSpec as ObserveSpec
from .rulespec import RuleSpec as RuleSpec
from .rulespec import Verdict as Verdict
from .suites import Bloat as Bloat
from .suites import Leakage as Leakage
from .suites import Overreach as Overreach
from .suites import Servility as Servility
from .words import GROUPS as GROUPS
from .words import LEXICONS as LEXICONS
from .words.domain import *
from .words.instruction import *
from .words.request import *
from .words.response import *

__version__ = "0.1.9"

_PYDANTIC_EVALS_SOURCE = {
    "Rule": "rule",
    "Observe": "rule",
    "PROSE": "suites",
    "ADHERENCE": "suites",
    "GENERIC": "suites",
}


def __getattr__(name: str) -> object:
    # deferred so importing lexguard never requires pydantic-evals until these are touched
    source = _PYDANTIC_EVALS_SOURCE.get(name)
    if source is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    try:
        module = import_module(f".{source}", __name__)
        return getattr(module, name)
    except ImportError as err:
        raise ImportError(
            f"lexguard.{name} needs pydantic-evals: pip install 'lexguard[pydantic-evals]'"
        ) from err
