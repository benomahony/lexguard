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

Each also surfaces two things beyond pass/fail, in whatever structured slot its framework gives a
check: which words matched (`Lexicon.hits(text)`, split into `indicated`/`ruled_out`) and how
dense that is (`Lexicon.density(text)`: the fraction of words that are hits, always in `[0, 1]`,
same split, but a real computed rate rather than a raw count — three "delve"s in one paragraph
reads as denser than one, even though `hits()` reports the same single term either way). pydantic-evals
gets `{Label}Indicated`/`{Label}RuledOut` labels plus
`{Label}IndicatedDensity`/`{Label}RuledOutDensity` scores, DeepEval and Inspect AI both fold the
density into `score_breakdown`/`Score.metadata`. The `ruled_out` side of all of these is only
emitted for a lexicon that actually has a `rules_out` list — most, like `Slop`, don't, so it stays
out of the way rather than showing a permanent zero. See each page's "Which terms fired" section.

`verdict.passed` is always exactly `True`/`False` — it can't say whether a reply barely failed or
is riddled with the problem. Two `Slop` hits in a three-sentence answer and two in a five-page
report both fail identically there, but their density won't match. Lean on `.density()` once
outputs get long enough that whether the concept appears at all stops being the interesting
question and how often it does becomes the one.

## Guardrails

A guard can only return one result, so this is the one place a `Bundle` genuinely combines
several lexicons into a single decision — a failure still lists every one that fired. Failures
retry by default, giving the model the reason and another attempt; pass `on_fail="block"` to
reject the value outright instead.

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
