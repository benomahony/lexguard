# DeepEval

`LexguardMetric` wraps a single `Lexicon` as a DeepEval `BaseMetric`, checked against
`actual_output`. Whether it asserts presence or absence is the lexicon's own `fail_when_neutral`
(see [writing a lexicon](../writing-a-lexicon.md#fail_when_neutral-what-a-match-means)). Score is
1.0 on a pass, 0.0 on a fail.

```py
from deepeval.test_case import LLMTestCase

from lexguard import Slop
from lexguard.integrations.evals.deepeval import LexguardMetric

metric = LexguardMetric(Slop)
test_case = LLMTestCase(
    input="explain caching",
    actual_output="Let us delve into the intricate tapestry of caching.",
)
print(metric.measure(test_case))
#> 0.0
print(metric.is_successful())
#> False
print(metric.reason)
"""
3 slop matches: "delve", "intricate", "tapestry"
  delve -> Let us delve into the intricate tapestry of ca…
  intricate -> Let us delve into the intricate tapestry of caching.
fix: swap for a plain verb or noun, or add these to the sampler ban list
"""
```

`metric.measure(test_case)` reads `test_case.actual_output` as the body. Pass the metric to
`evaluate()` or `assert_test()` like any other DeepEval metric. Check several lexicons by passing
several `LexguardMetric`s — each keeps its own score and reason, none of them merge.

## Hit density, not just pass/fail

`score` is always exactly 1.0 or 0.0 — it can't say whether a reply barely failed or is riddled
with the problem. `measure()` also fills DeepEval's own `score_breakdown` with `Lexicon.density()`:
the fraction of words that are hits (always in `[0, 1]`), split by which list they came from — a
real computed rate, not a raw count, so it stays comparable across replies of different lengths.

```py
from deepeval.test_case import LLMTestCase

from lexguard import Politeness
from lexguard.integrations.evals.deepeval import LexguardMetric

metric = LexguardMetric(Politeness)
test_case = LLMTestCase(input="fix the bug", actual_output="could you please fix the fucking bug")
metric.measure(test_case)
print(metric.score_breakdown)
#> {'indicated': 0.2857142857142857, 'ruled_out': 0.14285714285714285}
```

Two `Slop` hits in a three-sentence answer and two in a five-page report both score 0.0, but their
`score_breakdown["indicated"]` won't match — the first is a much higher density. Track it across a
`Dataset` once outputs get long enough that whether the concept appears at all stops being the
interesting question and how often it does becomes the one.

## Install

```bash
uv add "lexguard[deepeval]"
```
