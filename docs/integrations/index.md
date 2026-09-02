# Integrations

`Lexicon.verdict(text)` is the framework-agnostic core behind every integration
lexguard ships: the same lexicon and diagnosis text, checked once and wrapped in a few lines for
whichever eval framework a project already uses. It needs nothing installed at all.

```py
from lexguard import Slop

verdict = Slop.verdict("Let us delve into the intricate tapestry of caching.")
print(verdict.passed)
#> False
print(verdict.reason)
"""
3 slop matches: "delve", "intricate", "tapestry"
  delve -> Let us delve into the intricate tapestry of ca…
  intricate -> Let us delve into the intricate tapestry of caching.
fix: swap for a plain verb or noun, or add these to the sampler ban list
"""
```

A lexicon's own `fail_when_neutral` decides whether `verdict()` asserts presence or absence — not
a flag any integration takes; see
[writing a lexicon](../writing-a-lexicon.md#fail_when_neutral-what-a-match-means).

## Evals

An evaluator, metric, or scorer checks exactly one lexicon and reports under its own name — nothing
merges multiple lexicons into a single pass/fail, so checking several means listing several.

- [pydantic-evals](pydantic-evals.md): `LexguardEvaluator` wraps a `Lexicon` as an `Evaluator`
- [DeepEval](deepeval.md): `LexguardMetric` wraps a `Lexicon` as a `BaseMetric`
- [Inspect AI](inspect-ai.md): `lexguard_scorer` wraps a `Lexicon` as a `Scorer`

## Guardrails

A guard can only return one `allow`/`block`, so this is the one place a `Bundle` genuinely combines
several lexicons into a single decision — a block still lists every one that fired.

- [pydantic-ai-harness](pydantic-ai-harness.md): `lexguard_guard` wraps a `Lexicon` or `Bundle` as
  an `InputGuardrail`/`OutputGuardrail`/`ToolGuardrail` guard

## Install

Each integration is its own extra, so a project only pulls in what it actually uses:

```bash
uv add "lexguard[pydantic-evals]"
uv add "lexguard[deepeval]"
uv add "lexguard[inspect-ai]"
uv add "lexguard[pydantic-ai-harness]"
```

The core — `Lexicon`, `Bundle`, and `.signal()` / `.matches()` / `.denied()` / `.verdict()` — needs
none of them.
