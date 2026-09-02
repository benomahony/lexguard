---
name: lexguard
description: Help users work with lexguard. Use when the user asks about lexguard features, usage, or wants to check text (agent output, user requests, structured fields) for a concept like slop, sycophancy, disclaimers, or confidentiality — standalone, wired into an eval framework (pydantic-evals, DeepEval, Inspect AI), or wired into a guardrail (pydantic-ai-harness).
---

# lexguard Skill

lexguard is a library of lexicons: named sets of words and phrases that signal a concept, plus the
words that rule it out. Lexicons ship in the box covering both what a user asked for and what a
model produced. It is **not only** an evals add-on — the core matching API is plain functions over
a string with zero dependencies, useful anywhere you want to check text. pydantic-evals, DeepEval,
and Inspect AI evaluators, and a pydantic-ai-harness guardrail, are additional ways to run the same
checks, each behind its own optional extra.

## When to Use This Skill

Use this skill when:

- The user wants to detect slop, sycophancy, hedging, disclaimers, confidentiality leaks, or
  similar patterns in text (agent output or user requests)
- The user wants a guardrail, unit-test assertion, or log filter that fires on specific wording,
  with no framework involved
- The user is writing pydantic-evals `Dataset`/`Case`, DeepEval, or Inspect AI evaluations, or a
  pydantic-ai-harness guard, and wants lexguard's checks running alongside their own
- The user wants to define a lexicon for their own domain (`Lexicon(...)`, `|` to group lexicons
  into a `Bundle`)
- The user asks about lexguard's API, or `fail_when_neutral` (presence vs. absence)

## Ways to run a lexicon

**Standalone** — call `.signal()`, `.matches()`, or `.denied()` directly on a string. No framework
needs to be installed:

```python
from lexguard import Confidential


def guard(reply: str) -> str:
    if Confidential.matches(reply):
        raise ValueError("reply leaks a secret, blocking send")
    return reply
```

**Framework-agnostic** — `.verdict(text)` returns a pass/fail `Verdict` (with a `.reason` on
failure) with no framework at all. This is what every integration below wraps:

```python
from lexguard import Slop

verdict = Slop.verdict("let us delve in")
print(verdict.passed)
#> False
```

**pydantic-evals** — `LexguardEvaluator` wraps a `Lexicon` (or `Bundle`) as an `Evaluator`, for use
in a `Dataset`. Needs `lexguard[pydantic-evals]`:

```python
from pydantic_evals import Case, Dataset
from lexguard import Servility, Slop
from lexguard.integrations.evals.pydantic_evals import LexguardEvaluator

dataset = Dataset(
    name="prose",
    cases=[Case(name="explainer", inputs="explain database indexing")],
    evaluators=[LexguardEvaluator(Slop), LexguardEvaluator(Servility)],
)
```

**DeepEval** — `LexguardMetric` wraps a `Lexicon` as a `BaseMetric`. Needs `lexguard[deepeval]`:

```python
from deepeval.test_case import LLMTestCase
from lexguard import Slop
from lexguard.integrations.evals.deepeval import LexguardMetric

metric = LexguardMetric(Slop)
metric.measure(LLMTestCase(input="explain caching", actual_output="let us delve in"))
```

**Inspect AI** — `lexguard_scorer` wraps a `Lexicon` as a `Scorer`. Needs `lexguard[inspect-ai]`:

```python
from lexguard import Slop
from lexguard.integrations.evals.inspect_ai import lexguard_scorer

my_scorer = lexguard_scorer(Slop)
```

**pydantic-ai-harness** — `lexguard_guard` wraps a `Lexicon` (or `Bundle`) as an
`InputGuardrail`/`OutputGuardrail`/`ToolGuardrail` guard. Unlike the eval-framework adapters
above, a `Bundle` here genuinely combines into one decision, since that's the only shape a guard
can return. A failed verdict retries by default, handing the model the reason and another
attempt; pass `on_fail="block"` to reject the value outright instead (the right call for an
`InputGuardrail`, where there's no model output to retry). Needs `lexguard[pydantic-ai-harness]`:

```python
from pydantic_ai_harness.guardrails import OutputGuardrail
from lexguard import Slop
from lexguard.integrations.guardrails.pydantic_ai import lexguard_guard

guardrail = OutputGuardrail(guard=lexguard_guard(Slop))
```

## Core API

- `Lexicon.signal(text) -> Signal` — `present`, `denied`, or `absent` (three-valued, not boolean)
- `Lexicon.matches(text) -> bool` / `Lexicon(text)` — shorthand for `signal(text) is Signal.present`
- `Lexicon.denied(text) -> bool` — shorthand for `signal(text) is Signal.denied`
- `Lexicon.verdict(text) -> Verdict` — `passed: bool`, `reason: str | None` (framework-agnostic)
- `Lexicon.hits(text)` / `Lexicon.spans(text)` — the matched terms and their positions
- `Lexicon.examples(count=4)` — sample indicator phrases, for error messages
- `Lexicon.label` — the `PascalCase` name used as the report/assertion key
- `Lexicon.fail_when_neutral: bool` — set on construction; `False` (default) means `verdict()`
  fails when the concept is *present* (`Slop`, `Rudeness`, `Confidential`); `True` means it fails
  when the concept is *absent or denied* — silence is the problem (`Confirmation`, `Politeness`)
- `lexicon_a | lexicon_b` — a `Bundle`; `.signals(text)` reports each member separately
- `Observe([lexicons])` (pydantic-evals only) — records labels instead of assertions, for measuring
  before enforcing

## Prebuilt suites (`lexguard.suites`)

- `Bloat`, `Servility`, `Leakage`, `Overreach` — `Bundle`s grouping related output lexicons
- `PROSE` — the four bundles above, as a list of `LexguardEvaluator`s
- `ADHERENCE` — the unconditional instruction-following rules (`Disclaimer`, `Hedging`,
  `Anthropomorphic`)
- `GENERIC` — `PROSE + ADHERENCE`, a reasonable default suite (all three need
  `lexguard[pydantic-evals]`; build the same checks framework-agnostically with `.verdict()`)

## Resources

- [README.md](../../README.md) — install, the core API, and every way of running a lexicon
- [docs/writing-a-lexicon.md](../../docs/writing-a-lexicon.md) — building a `Lexicon` for your own
  domain, precision-over-recall, `rules_out`, and `fail_when_neutral`
- [docs/agents.md](../../docs/agents.md) — checking pydantic-ai agent output
- [docs/integrations/index.md](../../docs/integrations/index.md) — evals (pydantic-evals, DeepEval,
  Inspect AI) and guardrails (pydantic-ai-harness), each with its own page
- `src/lexguard/words/` — the shipped lexicons, grouped by `domain`, `instruction`, `request`,
  `response`
