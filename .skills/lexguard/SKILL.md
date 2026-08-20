---
name: lexguard
description: Help users work with lexguard. Use when the user asks about lexguard features, usage, or wants to check text (agent output, user requests, structured fields) for a concept like slop, sycophancy, disclaimers, or confidentiality — standalone, or wired into pydantic-evals, DeepEval, or Inspect AI.
---

# lexguard Skill

lexguard is a library of lexicons: named sets of words and phrases that signal a concept, plus the
words that rule it out. Ninety one ship in the box, covering both what a user asked for and what a
model produced. It is **not only** an evals add-on — the core matching API is plain functions over
a string with zero dependencies, useful anywhere you want to check text. pydantic-evals, DeepEval,
and Inspect AI evaluators are three additional ways to run the same checks, each behind its own
optional extra.

## When to Use This Skill

Use this skill when:

- The user wants to detect slop, sycophancy, hedging, disclaimers, confidentiality leaks, or
  similar patterns in text (agent output or user requests)
- The user wants a guardrail, unit-test assertion, or log filter that fires on specific wording,
  with no evals framework involved
- The user is writing pydantic-evals `Dataset`/`Case`, DeepEval, or Inspect AI evaluations and
  wants lexguard's checks running alongside their own
- The user wants to define a lexicon for their own domain (`Lexicon(...)`, `.extend()`, `|` to
  group lexicons)
- The user asks about lexguard's API, guards (`when`/`unless`), or scoping to a field
  (`field="notes"`, `field="items[]"`)

## Ways to run a lexicon

**Standalone** — call `.signal()`, `.fires()`, or `.denied()` directly on a string. No eval
framework needs to be installed:

```python
from lexguard import Confidential


def guard(reply: str) -> str:
    if Confidential.fires(reply):
        raise ValueError("reply leaks a secret, blocking send")
    return reply
```

**Framework-agnostic** — `.spec()` compiles a lexicon (or `Bundle`) into a `RuleSpec`, whose
`.check(output, inputs)` returns pass/fail `Verdict`s with no framework at all. This is what every
integration below wraps:

```python
from lexguard import Slop

verdicts = Slop.spec().check("let us delve in", "explain caching")
```

**pydantic-evals** — `.absent()` / `.expected()` compile the same lexicon into a `Rule`
(`Evaluator`), for use in a `Dataset`. Needs `lexguard[pydantic-evals]`:

```python
from pydantic_evals import Case, Dataset
from lexguard import Servility, Slop

dataset = Dataset(
    name="prose",
    cases=[Case(name="explainer", inputs="explain database indexing")],
    evaluators=[Slop.absent(), Servility.absent()],
)
```

**DeepEval** — `LexguardMetric` wraps a `RuleSpec` as a `BaseMetric`. Needs `lexguard[deepeval]`:

```python
from deepeval.test_case import LLMTestCase
from lexguard import Slop
from lexguard.integrations.deepeval import LexguardMetric

metric = LexguardMetric(Slop.spec())
metric.measure(LLMTestCase(input="explain caching", actual_output="let us delve in"))
```

**Inspect AI** — `lexguard_scorer` wraps a `RuleSpec` as a `Scorer`. Needs `lexguard[inspect-ai]`:

```python
from lexguard import Slop
from lexguard.integrations.inspect_ai import lexguard_scorer

my_scorer = lexguard_scorer(Slop.spec())
```

## Core API

- `Lexicon.signal(text) -> Signal` — `present`, `denied`, or `absent` (three-valued, not boolean)
- `Lexicon.fires(text) -> bool` — shorthand for `signal(text) is Signal.present`
- `Lexicon.denied(text) -> bool` — shorthand for `signal(text) is Signal.denied`
- `Lexicon.hits(text)` / `Lexicon.spans(text)` — the matched terms and their positions
- `Lexicon.examples(count=4)` — sample indicator phrases, for error messages
- `Lexicon.extend(indicates=..., rules_out=..., fix=...)` — a new lexicon layered on an existing one
- `lexicon_a | lexicon_b` — a `Bundle`; `.signals(text)` reports each member separately
- `Lexicon.spec(wanted=False, when=..., unless=..., field=...)` — build a framework-agnostic
  `RuleSpec`
- `Lexicon.absent(when=..., unless=..., field=...)` / `.expected(...)` — build a pydantic-evals
  `Rule` (an assertion)
- `Observe([lexicons])` — a pydantic-evals evaluator that records labels instead of assertions, for
  measuring before enforcing

## Prebuilt suites (`lexguard.suites`)

- `Bloat`, `Servility`, `Leakage`, `Overreach` — `Bundle`s grouping related output lexicons
- `PROSE` — the four bundles above, as a list of pydantic-evals evaluators
- `ADHERENCE` — guarded checks that the output honored what the request asked for
- `GENERIC` — `PROSE + ADHERENCE`, a reasonable default suite (all three suites need
  `lexguard[pydantic-evals]`; build the same checks framework-agnostically with `.spec()`)

## Resources

- [README.md](../../README.md) — install, the core API, and every way of running a lexicon
- [docs/writing-a-lexicon.md](../../docs/writing-a-lexicon.md) — building a `Lexicon` for your own
  domain, precision-over-recall, and `rules_out`
- [docs/rules.md](../../docs/rules.md) — `.absent()`/`.expected()`, `when`/`unless` guards, field
  scoping, `Observe`
- [docs/agents.md](../../docs/agents.md) — checking pydantic-ai agent output, plain or structured
- [docs/integrations.md](../../docs/integrations.md) — `RuleSpec`, DeepEval, and Inspect AI
- `src/lexguard/words/` — the shipped lexicons, grouped by `domain`, `instruction`, `request`,
  `response`
