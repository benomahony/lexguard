"""Mine lexicon candidates from labelled OTel traces.

Point it at GenAI-instrumented traces with a success/failure signal (a live LLM judge, a stored
eval verdict, a heuristic) and it ranks the words and phrases whose presence tracks failure,
adjusted for confounders you name, and splits them into `indicates` and `rules_out` candidates for
you to curate into a `Lexicon`.

Works offline and online. Offline, `mine()` takes a batch of pre-labelled production traces at
once. Online, a `Miner` accumulates evidence as you `observe()` traces one at a time, labelling
each with anything you like, and `suggest()` reports from whatever it has seen so far.

Zero third-party dependencies, like the core: OTLP is JSON and the statistics are stdlib maths.
"""

from __future__ import annotations

from .labels import Label as Label
from .labels import Labeller as Labeller
from .labels import from_attribute as from_attribute
from .labels import normalize as normalize
from .report import DEFAULT_LENGTH_EDGES as DEFAULT_LENGTH_EDGES
from .report import STOPWORDS as STOPWORDS
from .report import Candidate as Candidate
from .report import Miner as Miner
from .report import Scorecard as Scorecard
from .report import Suggestions as Suggestions
from .report import evaluate as evaluate
from .report import mine as mine
from .stats import Association as Association
from .stats import associate as associate
from .stats import fdr as fdr
from .traces import GROUP as GROUP
from .traces import Message as Message
from .traces import Trace as Trace
from .traces import extract_traces as extract_traces

__all__ = [
    "Association",
    "Candidate",
    "DEFAULT_LENGTH_EDGES",
    "GROUP",
    "Label",
    "Labeller",
    "Message",
    "Miner",
    "STOPWORDS",
    "Scorecard",
    "Suggestions",
    "Trace",
    "associate",
    "evaluate",
    "extract_traces",
    "fdr",
    "from_attribute",
    "mine",
    "normalize",
]
