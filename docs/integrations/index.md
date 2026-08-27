# Integrations

`Check` is the framework-agnostic core behind every integration lexguard ships: the same
lexicons, guards, and diagnosis text, compiled once and handed to whichever eval framework a
project already uses. `Lexicon.check()` / `Bundle.check()` build one directly, with no framework
installed at all.

```py
from lexguard import Slop

verdicts = Slop.check().run(
    "Let us delve into the intricate tapestry of caching.", "explain caching"
)
print(verdicts[0].passed)
#> False
print(verdicts[0].reason)
"""
3 slop matches: "delve", "intricate", "tapestry"
  delve -> Let us delve into the intricate tapestry of ca…
  intricate -> Let us delve into the intricate tapestry of caching.
fix: swap for a plain verb or noun, or add these to the sampler ban list
"""
```

`run(output, inputs)` takes the same `wanted`, `when`, `unless`, `field`, and `of` as
`.absent()` / `.expected()`; see [Rules](../rules.md). It returns `None` rather than a list when a
guard did not fire or the scoped field was empty — the same silence-is-not-a-failure rule as
everywhere else in lexguard, so every adapter below treats a skipped spec as a pass, not a fail.

## Frameworks

- [pydantic-evals](pydantic-evals.md): `.absent()` / `.expected()` build a `Rule` directly
- [DeepEval](deepeval.md): `LexguardMetric` wraps a `Check` as a `BaseMetric`
- [Inspect AI](inspect-ai.md): `lexguard_scorer` wraps a `Check` as a `Scorer`

## Install

Each integration is its own extra, so a project only pulls in the eval framework it actually uses:

```bash
uv add "lexguard[pydantic-evals]"
uv add "lexguard[deepeval]"
uv add "lexguard[inspect-ai]"
```

The core — `Lexicon`, `Bundle`, `.signal()` / `.fires()` / `.denied()`, and `.check()` — needs none
of them.
