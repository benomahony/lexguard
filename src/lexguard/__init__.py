from __future__ import annotations

from importlib import import_module

from .checks import Check as Check
from .checks import Observation as Observation
from .checks import Verdict as Verdict
from .lexicon import Bundle as Bundle
from .lexicon import Lexicon as Lexicon
from .lexicon import Signal as Signal
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

__version__ = "0.1.13"

# the shipped suites are pydantic-evals evaluator lists; deferred so importing lexguard never
# requires pydantic-evals until one is touched. the evaluators themselves live in
# lexguard.integrations.pydantic_evals, not at the top level.
_SUITES = ("PROSE", "ADHERENCE", "GENERIC")


def __getattr__(name: str) -> object:
    assert name, "attribute name must not be empty"
    if name not in _SUITES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    try:
        return vars(import_module(".suites", __name__))["__getattr__"](name)
    except ImportError as err:
        raise ImportError(
            f"lexguard.{name} needs pydantic-evals: pip install 'lexguard[pydantic-evals]'"
        ) from err
