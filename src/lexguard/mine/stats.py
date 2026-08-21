from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

# A 2x2 contingency for one stratum: how a phrase's presence lines up with the outcome.
# (present_fail, present_ok, absent_fail, absent_ok)
Table = tuple[int, int, int, int]


@dataclass(frozen=True)
class Association:
    """How strongly a phrase's presence tracks failure, pooled across confounder strata.

    `odds_ratio` is the Mantel-Haenszel estimate: > 1 means presence raises the odds of failure
    with the strata (task, length, model, ...) held fixed, < 1 means it tracks success. When only
    one stratum is supplied this is the plain crude odds ratio, so the confounder-adjusted and the
    naive case share one code path.
    """

    odds_ratio: float
    log_odds: float
    z: float
    p: float
    support: int  # rows (traces) where the phrase is present, summed over strata

    def __post_init__(self) -> None:
        assert self.odds_ratio >= 0.0, "an odds ratio is never negative"
        assert 0.0 <= self.p <= 1.0, "a p-value is a probability"
        assert self.support >= 0


def associate(tables: Sequence[Table]) -> Association:
    """Pool per-stratum 2x2 tables into one Mantel-Haenszel odds ratio.

    The variance of its log follows Robins-Breslow-Greenland, so the z-score stays valid across
    sparse strata. A stratum with any empty cell gets a Haldane-Anscombe 0.5 correction rather
    than collapsing the whole estimate to 0 or infinity.
    """
    r = s = 0.0
    pr = ps = qr = qs = 0.0
    support = 0
    for present_fail, present_ok, absent_fail, absent_ok in tables:
        support += present_fail + present_ok
        a, b, c, d = present_fail, present_ok, absent_fail, absent_ok
        n = a + b + c + d
        # a stratum with an empty margin (the phrase never appears, or the outcome never varies)
        # says nothing about the association; skip it rather than invent cells for it
        if 0 in (a + b, c + d, a + c, b + d):
            continue
        if 0 in (a, b, c, d):
            a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
            n = a + b + c + d
        rk = a * d / n
        sk = b * c / n
        pk = (a + d) / n
        qk = (b + c) / n
        r += rk
        s += sk
        pr += pk * rk
        ps += pk * sk
        qr += qk * rk
        qs += qk * sk
    if r <= 0.0 or s <= 0.0:
        # no discordant mass to compare; report "no signal" rather than a divide-by-zero
        return Association(odds_ratio=1.0, log_odds=0.0, z=0.0, p=1.0, support=support)
    odds_ratio = r / s
    log_odds = math.log(odds_ratio)
    variance = pr / (2 * r * r) + (ps + qr) / (2 * r * s) + qs / (2 * s * s)
    z = log_odds / math.sqrt(variance) if variance > 0.0 else 0.0
    p = math.erfc(abs(z) / math.sqrt(2))
    result = Association(odds_ratio=odds_ratio, log_odds=log_odds, z=z, p=p, support=support)
    assert (result.log_odds > 0) == (result.odds_ratio > 1) or result.odds_ratio == 1
    return result


def fdr(scores: dict[str, float]) -> dict[str, float]:
    """Benjamini-Hochberg adjusted p-values (q-values) over every phrase tested at once.

    Thousands of candidate phrases means thousands of tests, so a raw p-value of 0.01 is not a
    finding. The q-value is the false-discovery rate you accept by keeping a phrase and everything
    ranked above it.
    """
    m = len(scores)
    if m == 0:
        return {}
    order = sorted(scores.items(), key=lambda item: item[1])
    result: dict[str, float] = {}
    running = 1.0
    for rank in range(m - 1, -1, -1):
        key, p = order[rank]
        running = min(running, p * m / (rank + 1))
        result[key] = running
    assert set(result) == set(scores)
    assert all(0.0 <= q <= 1.0 for q in result.values())
    return result
