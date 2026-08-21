from __future__ import annotations

import re
from collections import Counter, deque
from collections.abc import Sequence
from dataclasses import dataclass

from ..lexicon import WORD_PATTERN, Lexicon, fold, snippet
from .labels import Label, Labeller, normalize
from .stats import associate, fdr
from .traces import Trace

_TOKEN = re.compile(WORD_PATTERN)
_UNSET = object()

# Length thresholds (in tokens) for the synthetic "length" confounder. Fixed rather than derived
# from the data so a trace lands in the same bucket online and offline, whatever else has streamed
# past. Override with Miner(length_edges=...).
DEFAULT_LENGTH_EDGES = (40, 120, 300)

# Bare function words correlate with a register (apologetic, hedging) without being the wording a
# lexicon should fire on, and they crowd out the content phrases. Dropped as unigram candidates
# only: a multiword phrase like "not sure" or "i'm sorry" still stands. Override via `stopwords=`.
STOPWORDS = frozenset(
    "a an and are as at be been being but by can could did do does for from had has have "
    "he her him his i i'm if in into is it it's its me my no not of on or our so than that "
    "the their them then there they this to up us was we were what when which who will with "
    "would you your".split()
)


@dataclass(frozen=True)
class Candidate:
    """One phrase the mine surfaced, with the evidence a curator needs to keep or drop it.

    `odds_ratio` is confounder-adjusted when the mine was given confounders. `leaning` says which
    list it belongs in: `failure` phrases are `indicates` candidates, `success` phrases co-occur
    with the concept vocabulary but land in wins, so they are `rules_out` candidates.
    """

    phrase: str
    leaning: Label
    odds_ratio: float
    z: float
    q: float
    support: int
    failure_rate: float
    base_rate: float
    examples: tuple[str, ...]

    def __post_init__(self) -> None:
        assert self.leaning in (Label.failure, Label.success)
        assert self.support > 0


@dataclass(frozen=True)
class Suggestions:
    """The ranked output of a mine: two lists of `Candidate`, plus what to curate them into."""

    indicates: tuple[Candidate, ...]
    rules_out: tuple[Candidate, ...]
    group: str
    base_rate: float
    n: int

    def __repr__(self) -> str:
        return (
            f"Suggestions(group={self.group!r}, n={self.n}, base_rate={self.base_rate:.2f}, "
            f"{len(self.indicates)} indicates, {len(self.rules_out)} rules_out)"
        )

    def suggest(self, name: str, fix: str = "", limit: int = 20) -> Lexicon:
        """Assemble the top candidates into a `Lexicon` to hand-edit, not to ship as-is."""
        return Lexicon(
            name=name,
            indicates=[c.phrase for c in self.indicates[:limit]],
            rules_out=[c.phrase for c in self.rules_out[:limit]],
            fix=fix,
        )


def _ngrams(tokens: Sequence[str], max_ngram: int) -> frozenset[str]:
    grams: set[str] = set()
    for n in range(1, max_ngram + 1):
        for i in range(len(tokens) - n + 1):
            grams.add(" ".join(tokens[i : i + n]))
    return frozenset(grams)


def _length_bucket(count: int, edges: Sequence[int]) -> int:
    bucket = 0
    for edge in edges:
        if count > edge:
            bucket += 1
    return bucket


def _snippets(
    phrase: str, recent: Sequence[tuple[str, bool]], failed: bool, limit: int
) -> tuple[str, ...]:
    pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
    found: list[str] = []
    for body, body_failed in recent:
        if body_failed is not failed:
            continue
        match = pattern.search(body)
        if match:
            found.append(snippet(body, match.start(), match.end()))
        if len(found) >= limit:
            break
    return tuple(found)


def _contained(short: str, long: str) -> bool:
    a, b = short.split(" "), long.split(" ")
    if len(a) >= len(b):
        return False
    return any(b[i : i + len(a)] == a for i in range(len(b) - len(a) + 1))


def _prune(candidates: Sequence[Candidate]) -> list[Candidate]:
    # between nested phrases ("delve" vs "delve into"), keep the stronger discriminator; a tie
    # keeps the shorter, more general one
    drop: set[str] = set()
    for a in candidates:
        for b in candidates:
            if a.phrase == b.phrase or a.phrase in drop or b.phrase in drop:
                continue
            short, long = sorted((a, b), key=lambda c: len(c.phrase.split(" ")))
            if not _contained(short.phrase, long.phrase):
                continue
            drop.add(long.phrase if abs(short.z) >= abs(long.z) else short.phrase)
    return [c for c in candidates if c.phrase not in drop]


class Miner:
    """A running mine you feed one trace at a time, online or offline.

    Every statistic it needs is an additive counter, so `observe()` folds a trace into per-stratum
    contingency tables and forgets the trace itself (keeping only a bounded window of bodies for
    example snippets). Offline you `extend()` a batch of pre-labelled production traces; online you
    `observe(trace, verdict)` as each run lands, labelling with anything — a live LLM judge, a
    heuristic, a human. Call `suggest()` at any point to score the evidence gathered so far.

    The counters are plain dicts, so a long-running miner's state pickles for checkpointing.
    """

    def __init__(
        self,
        *,
        group: str = "response",
        confounders: Sequence[str] = (),
        max_ngram: int = 3,
        length_edges: Sequence[int] = DEFAULT_LENGTH_EDGES,
        keep_examples: int = 1000,
        label: Labeller | None = None,
    ) -> None:
        self.group = group
        self.confounders = tuple(confounders)
        self.max_ngram = max_ngram
        self.length_edges = tuple(length_edges)
        self.label = label
        self.strata_totals: dict[tuple[object, ...], list[int]] = {}  # stratum -> [fail, ok]
        self.present: dict[str, dict[tuple[object, ...], list[int]]] = {}  # gram -> stratum -> pair
        self.support: Counter[str] = Counter()
        self.recent: deque[tuple[str, bool]] = deque(maxlen=max(1, keep_examples))
        self.n = 0
        self.failures = 0

    def __repr__(self) -> str:
        return f"Miner(group={self.group!r}, n={self.n}, base_rate={self.base_rate:.2f})"

    @property
    def base_rate(self) -> float:
        return self.failures / self.n if self.n else 0.0

    def _stratum(self, trace: Trace, n_tokens: int) -> tuple[object, ...]:
        parts = tuple(trace.attributes.get(key) for key in self.confounders if key != "length")
        if "length" in self.confounders:
            parts = (*parts, _length_bucket(n_tokens, self.length_edges))
        return parts

    def observe(self, trace: Trace, outcome: object = _UNSET) -> Miner:
        """Fold one trace in under its outcome; returns self so calls chain.

        Pass `outcome` as anything `normalize` accepts (a `Label`, bool, "pass"/"fail", 0/1) — this
        is the online path where you label with any judge you like. Omit it to apply the `label`
        callable the miner was constructed with. An abstaining outcome (`None`/`Label.abstain`)
        drops the trace, mirroring a lexicon that records nothing when it does not apply.
        """
        if outcome is _UNSET:
            assert self.label is not None, "pass an outcome, or construct Miner(label=...)"
            result = normalize(self.label(trace))
        else:
            result = normalize(outcome)  # type: ignore[arg-type]
        if result is Label.abstain:
            return self
        body = trace.text(self.group)
        tokens = _TOKEN.findall(fold(body))
        stratum = self._stratum(trace, len(tokens))
        failed = result is Label.failure
        idx = 0 if failed else 1
        self.strata_totals.setdefault(stratum, [0, 0])[idx] += 1
        for gram in _ngrams(tokens, self.max_ngram):
            self.present.setdefault(gram, {}).setdefault(stratum, [0, 0])[idx] += 1
            self.support[gram] += 1
        self.recent.append((body, failed))
        self.n += 1
        self.failures += failed
        return self

    def extend(self, traces: Sequence[Trace], label: Labeller | None = None) -> Miner:
        """Fold in a batch, labelling each trace with `label` (or the miner's own `label`)."""
        labeller = label or self.label
        assert labeller is not None, "extend needs a label, or construct Miner(label=...)"
        for trace in traces:
            self.observe(trace, labeller(trace))
        return self

    def suggest(
        self,
        *,
        min_support: int = 3,
        fdr_max: float = 0.1,
        examples: int = 3,
        stopwords: frozenset[str] = STOPWORDS,
    ) -> Suggestions:
        """Score everything observed so far and split it into `indicates` / `rules_out`.

        Recomputed from the counters on each call, so it is cheap to poll a live miner. Bare
        function words are dropped as unigram candidates; phrases surviving the `fdr_max`
        false-discovery cut are ranked by how strongly their presence tracks failure.
        """
        assert min_support >= 1
        base_rate = self.base_rate
        scored: dict[str, Candidate] = {}
        pvalues: dict[str, float] = {}
        for gram, per_stratum in self.present.items():
            if self.support[gram] < min_support:
                continue
            if " " not in gram and gram in stopwords:
                continue
            tables = []
            for stratum, (fail, ok) in self.strata_totals.items():
                pf, po = per_stratum.get(stratum, (0, 0))
                tables.append((pf, po, fail - pf, ok - po))
            assoc = associate(tables)
            if assoc.odds_ratio == 1.0 or assoc.support == 0:
                continue
            pvalues[gram] = assoc.p
            present_fail = sum(pf for pf, _, _, _ in tables)
            scored[gram] = Candidate(
                phrase=gram,
                leaning=Label.failure if assoc.odds_ratio > 1 else Label.success,
                odds_ratio=assoc.odds_ratio,
                z=assoc.z,
                q=1.0,  # replaced from the FDR pass below
                support=assoc.support,
                failure_rate=present_fail / assoc.support,
                base_rate=base_rate,
                examples=(),
            )
        qvalues = fdr(pvalues)
        kept: list[Candidate] = []
        for gram, candidate in scored.items():
            if qvalues[gram] > fdr_max:
                continue
            failed = candidate.leaning is Label.failure
            kept.append(
                Candidate(
                    phrase=candidate.phrase,
                    leaning=candidate.leaning,
                    odds_ratio=candidate.odds_ratio,
                    z=candidate.z,
                    q=qvalues[gram],
                    support=candidate.support,
                    failure_rate=candidate.failure_rate,
                    base_rate=candidate.base_rate,
                    examples=_snippets(gram, self.recent, failed, examples),
                )
            )
        ranked = sorted(kept, key=lambda c: (-abs(c.z), -c.support, c.phrase))
        return Suggestions(
            indicates=tuple(_prune([c for c in ranked if c.leaning is Label.failure])),
            rules_out=tuple(_prune([c for c in ranked if c.leaning is Label.success])),
            group=self.group,
            base_rate=base_rate,
            n=self.n,
        )


def mine(
    traces: Sequence[Trace],
    *,
    label: Labeller,
    group: str = "response",
    confounders: Sequence[str] = (),
    min_support: int = 3,
    max_ngram: int = 3,
    fdr_max: float = 0.1,
    examples: int = 3,
    stopwords: frozenset[str] = STOPWORDS,
    length_edges: Sequence[int] = DEFAULT_LENGTH_EDGES,
) -> Suggestions:
    """Mine a batch of pre-labelled traces in one call: a `Miner` fed all of `traces`, then asked.

    `label` is any `Trace -> outcome` callable (`from_attribute(...)` over a stored verdict, a live
    LLM judge, a heuristic). `confounders` names trace attributes to stratify on so a phrase that
    merely marks a hard task or a long answer is not mistaken for a failure signal; the synthetic
    name `"length"` stratifies on answer length. Phrases surviving the `fdr_max` false-discovery cut
    split into `indicates` (failure-leaning) and `rules_out` (success-leaning). For streaming
    production traces, build a `Miner` and `observe()` them as they arrive instead. Either way the
    result is a starting point for curation, not a finished lexicon.
    """
    miner = Miner(
        group=group,
        confounders=confounders,
        max_ngram=max_ngram,
        length_edges=length_edges,
        keep_examples=max(1000, len(traces)),
    )
    miner.extend(traces, label)
    return miner.suggest(
        min_support=min_support, fdr_max=fdr_max, examples=examples, stopwords=stopwords
    )


@dataclass(frozen=True)
class Scorecard:
    """How a lexicon does at predicting failure on held-out traces."""

    precision: float
    recall: float
    f1: float
    support: int  # traces the lexicon fired on
    n: int

    def __post_init__(self) -> None:
        assert 0.0 <= self.precision <= 1.0 and 0.0 <= self.recall <= 1.0


def evaluate(
    lexicon: Lexicon,
    traces: Sequence[Trace],
    *,
    label: Labeller,
    group: str = "response",
) -> Scorecard:
    """Score a mined lexicon on held-out traces: does firing actually predict failure?

    Mining and evaluating on the same traces just measures memorisation. Split the traces, mine on
    one half, and call this on the other to see whether the phrases generalise.
    """
    tp = fp = fn = 0
    n = 0
    for trace in traces:
        outcome = normalize(label(trace))
        if outcome is Label.abstain:
            continue
        n += 1
        fired = lexicon.fires(trace.text(group))
        failed = outcome is Label.failure
        tp += fired and failed
        fp += fired and not failed
        fn += not fired and failed
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return Scorecard(precision=precision, recall=recall, f1=f1, support=tp + fp, n=n)
