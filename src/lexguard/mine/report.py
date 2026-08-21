from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from ..lexicon import WORD_PATTERN, Lexicon, fold, snippet
from .labels import Label, Labeller, normalize
from .stats import Table, associate, fdr
from .traces import Trace

_TOKEN = re.compile(WORD_PATTERN)

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
    """The ranked output of `mine()`: two lists of `Candidate`, plus what to curate them into."""

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


@dataclass(frozen=True)
class _Row:
    body: str
    tokens: tuple[str, ...]
    ngrams: frozenset[str]
    failed: bool
    stratum: tuple[object, ...]


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


def _rows(
    traces: Sequence[Trace], label: Labeller, group: str, confounders: Sequence[str], max_ngram: int
) -> list[_Row]:
    staged: list[tuple[str, tuple[str, ...], bool, tuple[object, ...]]] = []
    lengths: list[int] = []
    want_length = "length" in confounders
    for trace in traces:
        outcome = normalize(label(trace))
        if outcome is Label.abstain:
            continue
        body = trace.text(group)
        tokens = tuple(_TOKEN.findall(fold(body)))
        strata = tuple(trace.attributes.get(key) for key in confounders if key != "length")
        staged.append((body, tokens, outcome is Label.failure, strata))
        lengths.append(len(tokens))
    edges = _quartiles(lengths) if want_length else ()
    rows: list[_Row] = []
    for (body, tokens, failed, strata), length in zip(staged, lengths):
        stratum = tuple(strata)
        if want_length:
            stratum = (*stratum, _length_bucket(length, edges))
        rows.append(_Row(body, tokens, _ngrams(tokens, max_ngram), failed, stratum))
    return rows


def _quartiles(values: Sequence[int]) -> tuple[int, ...]:
    if not values:
        return ()
    ordered = sorted(values)
    return tuple(ordered[min(len(ordered) - 1, len(ordered) * q // 4)] for q in (1, 2, 3))


def _tables(rows: Sequence[_Row]) -> tuple[dict[str, list[Table]], Counter[str]]:
    strata_totals: dict[tuple[object, ...], list[int]] = defaultdict(lambda: [0, 0])  # [fail, ok]
    present: dict[str, dict[tuple[object, ...], list[int]]] = defaultdict(
        lambda: defaultdict(lambda: [0, 0])
    )
    support: Counter[str] = Counter()
    for row in rows:
        strata_totals[row.stratum][0 if row.failed else 1] += 1
        for gram in row.ngrams:
            present[gram][row.stratum][0 if row.failed else 1] += 1
            support[gram] += 1
    tables: dict[str, list[Table]] = {}
    for gram, per_stratum in present.items():
        rows_for_gram: list[Table] = []
        for stratum, (fail_total, ok_total) in strata_totals.items():
            pf, po = per_stratum.get(stratum, [0, 0])
            rows_for_gram.append((pf, po, fail_total - pf, ok_total - po))
        tables[gram] = rows_for_gram
    return tables, support


def _snippets(phrase: str, rows: Sequence[_Row], failed: bool, limit: int) -> tuple[str, ...]:
    pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
    found: list[str] = []
    for row in rows:
        if row.failed is not failed:
            continue
        match = pattern.search(row.body)
        if match:
            found.append(snippet(row.body, match.start(), match.end()))
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
) -> Suggestions:
    """Rank phrases in `group` by how their presence tracks failure, adjusted for `confounders`.

    `label` is any `Trace -> outcome` callable (a live LLM judge, `from_attribute(...)` over a
    stored verdict, a heuristic). `confounders` names trace attributes to stratify on so a phrase
    that merely marks a hard task or a long answer is not mistaken for a failure signal; the
    synthetic name `"length"` stratifies on answer length. Bare function words are dropped as
    unigram candidates (see `stopwords`); phrases containing them survive. Phrases surviving the
    `fdr_max` false-discovery cut split into `indicates` (failure-leaning) and `rules_out`
    (success-leaning). The result is a starting point for curation, not a finished lexicon.
    """
    rows = _rows(traces, label, group, confounders, max_ngram)
    assert min_support >= 1
    total = len(rows)
    failures = sum(row.failed for row in rows)
    base_rate = failures / total if total else 0.0
    tables, support = _tables(rows)
    scored: dict[str, tuple[Candidate, float]] = {}
    pvalues: dict[str, float] = {}
    for gram, gram_tables in tables.items():
        if support[gram] < min_support:
            continue
        if " " not in gram and gram in stopwords:
            continue
        assoc = associate(gram_tables)
        if assoc.odds_ratio == 1.0 or assoc.support == 0:
            continue
        pvalues[gram] = assoc.p
        present_fail = sum(pf for pf, _, _, _ in gram_tables)
        scored[gram] = (
            Candidate(
                phrase=gram,
                leaning=Label.failure if assoc.odds_ratio > 1 else Label.success,
                odds_ratio=assoc.odds_ratio,
                z=assoc.z,
                q=1.0,  # filled from the FDR pass below
                support=assoc.support,
                failure_rate=present_fail / assoc.support if assoc.support else 0.0,
                base_rate=base_rate,
                examples=(),
            ),
            assoc.p,
        )
    qvalues = fdr(pvalues)
    kept: list[Candidate] = []
    for gram, (candidate, _) in scored.items():
        q = qvalues[gram]
        if q > fdr_max:
            continue
        failed = candidate.leaning is Label.failure
        kept.append(
            Candidate(
                phrase=candidate.phrase,
                leaning=candidate.leaning,
                odds_ratio=candidate.odds_ratio,
                z=candidate.z,
                q=q,
                support=candidate.support,
                failure_rate=candidate.failure_rate,
                base_rate=candidate.base_rate,
                examples=_snippets(gram, rows, failed, examples),
            )
        )
    ranked = sorted(kept, key=lambda c: (-abs(c.z), -c.support, c.phrase))
    indicates = _prune([c for c in ranked if c.leaning is Label.failure])
    rules_out = _prune([c for c in ranked if c.leaning is Label.success])
    return Suggestions(
        indicates=tuple(indicates),
        rules_out=tuple(rules_out),
        group=group,
        base_rate=base_rate,
        n=total,
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
