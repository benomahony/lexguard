# DeepEval

`LexguardMetric` wraps a `RuleSpec` as a DeepEval `BaseMetric`. Its score is the fraction of
lexicons in the spec that passed; the default `threshold=1.0` means every one of them must, the
same all-or-nothing semantics `.absent()` gives a `Bundle`.

```py
from deepeval.test_case import LLMTestCase

from lexguard import Slop
from lexguard.integrations.deepeval import LexguardMetric

metric = LexguardMetric(Slop.spec())
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

`metric.measure(test_case)` reads `test_case.actual_output` (or `field=...` scoped into it) as the
body and `test_case.input` as the request a `when` / `unless` guard checks against. Pass the
metric to `evaluate()` or `assert_test()` like any other DeepEval metric.

## Install

```bash
uv add "lexguard[deepeval]"
```
