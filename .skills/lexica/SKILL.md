---
name: lexica
description: Help users work with lexica. Use when the user asks about lexica features, usage, or wants to check text (agent output, user requests, structured fields) for a concept like slop, sycophancy, disclaimers, or confidentiality — with or without pydantic-evals.
---

# lexica Skill

lexica is a library of lexicons: named sets of words and phrases that signal a concept, plus the
words that rule it out. Ninety one ship in the box, covering both what a user asked for and what a
model produced. It is **not only** a pydantic-evals add-on — the core matching API is plain
functions over a string, useful anywhere you want to check text, and pydantic-evals evaluators are
one additional way to run the same checks.

## When to Use This Skill

Use this skill when:

- The user wants to detect slop, sycophancy, hedging, disclaimers, confidentiality leaks, or
  similar patterns in text (agent output or user requests)
- The user wants a guardrail, unit-test assertion, or log filter that fires on specific wording,
  with no evals framework involved
- The user is writing pydantic-evals `Dataset`/`Case` evaluations and wants lexica's evaluators
  alongside their own
- The user wants to define a lexicon for their own domain (`Lexicon(...)`, `.extend()`, `|` to
  group lexicons)
- The user asks about lexica's API, guards (`when`/`unless`), or scoping to a field
  (`field="notes"`, `field="items[]"`)

## Two ways to run a lexicon

**Standalone** — call `.signal()`, `.fires()`, or `.denied()` directly on a string. No `Dataset`,
no `Case`, nothing from pydantic-evals needs to run:

```python
from lexica import Confidential


def guard(reply: str) -> str:
    if Confidential.fires(reply):
        raise ValueError("reply leaks a secret, blocking send")
    return reply
```

**Inside pydantic-evals** — `.absent()` / `.expected()` compile the same lexicon into an
`Evaluator`, for use in a `Dataset`:

```python
from pydantic_evals import Case, Dataset
from lexica import Servility, Slop

dataset = Dataset(
    name="prose",
    cases=[Case(name="explainer", inputs="explain database indexing")],
    evaluators=[Slop.absent(), Servility.absent()],
)
```

## Core API

- `Lexicon.signal(text) -> Signal` — `present`, `denied`, or `absent` (three-valued, not boolean)
- `Lexicon.fires(text) -> bool` — shorthand for `signal(text) is Signal.present`
- `Lexicon.denied(text) -> bool` — shorthand for `signal(text) is Signal.denied`
- `Lexicon.hits(text)` / `Lexicon.spans(text)` — the matched terms and their positions
- `Lexicon.examples(count=4)` — sample indicator phrases, for error messages
- `Lexicon.extend(indicates=..., rules_out=..., fix=...)` — a new lexicon layered on an existing one
- `lexicon_a | lexicon_b` — a `Bundle`; `.signals(text)` reports each member separately
- `Lexicon.absent(when=..., unless=..., field=...)` / `.expected(...)` — build a pydantic-evals
  `Rule` (an assertion)
- `Observe([lexicons])` — a pydantic-evals evaluator that records labels instead of assertions, for
  measuring before enforcing

## Prebuilt suites (`lexica.suites`)

- `Bloat`, `Servility`, `Leakage`, `Overreach` — `Bundle`s grouping related output lexicons
- `PROSE` — the four bundles above, as a list of evaluators
- `ADHERENCE` — guarded checks that the output honored what the request asked for
- `GENERIC` — `PROSE + ADHERENCE`, a reasonable default suite

## Resources

- [README.md](../../README.md) — install, the core API, both standalone and pydantic-evals usage
- [docs/writing-a-lexicon.md](../../docs/writing-a-lexicon.md) — building a `Lexicon` for your own
  domain, precision-over-recall, and `rules_out`
- [docs/rules.md](../../docs/rules.md) — `.absent()`/`.expected()`, `when`/`unless` guards, field
  scoping, `Observe`
- [docs/agents.md](../../docs/agents.md) — checking pydantic-ai agent output, plain or structured
- `src/lexica/words/` — the shipped lexicons, grouped by `domain`, `instruction`, `request`,
  `response`
