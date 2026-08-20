<p align="center">
  <img src="docs/assets/lexguard.png" alt="lexguard" width="50%">
</p>

# Lexguard

Lexicons that score text for a concept, plus evaluators for
[pydantic-evals](https://ai.pydantic.dev/evals/), [DeepEval](https://deepeval.com/), and
[Inspect AI](https://inspect.aisi.org.uk/) built on top.

A lexicon is a named set of words and phrases that signal a concept, plus the words that rule it out.
Ninety one of them ship in the box, covering what a user asked for and what a model produced.
`.signal()`, `.fires()` and `.denied()` are plain functions over text: call them directly in a
guardrail, a test, a CLI, or a log pipeline, no evals framework required. `.spec()` compiles the
same lexicon into a framework-agnostic `RuleSpec`, which `.absent()` / `.expected()` and the
[integrations](docs/integrations/index.md) turn into an evaluator for whichever framework you use.

## Install

```bash
uv add lexguard
```

The core has no dependencies. Each eval framework is its own extra:

```bash
uv add "lexguard[pydantic-evals]"
uv add "lexguard[deepeval]"
uv add "lexguard[inspect-ai]"
```

## The idea

A lexicon on its own only observes. Naming a polarity turns it into a verdict.

```py
from lexguard import Slop

print(Slop.signal("let us delve into the intricate tapestry"))
#> present
print(Slop.signal("caching skips repeated work"))
#> absent
```

Lexicons are three valued, not two. `rules_out` exists so that wording which merely shares
vocabulary with a concept does not count as the concept.

```py
from lexguard import HighPriority, Recurrence

print(Recurrence.signal("bin day every tuesday"))
#> present
print(Recurrence.signal("i do that every so often"))
#> denied
print(HighPriority.signal("sort it whenever, no rush"))
#> denied
```

`denied` is not the same as `absent`. An agent setting `priority=high` on "no rush" is wrong,
where on a sentence with no priority wording at all it is merely unasked for.

## Using it without an evals framework

`signal()`, `fires()` and `denied()` are the whole API surface at this layer: plain calls over a
string. Nothing here needs `Dataset`, `Case`, or pydantic-evals in general, so a lexicon works just
as well as a guardrail before a response goes out, a plain `assert` in a unit test, or a filter in
a log pipeline.

```py
from lexguard import Confidential


def guard(reply: str) -> str:
    if Confidential.fires(reply):
        raise ValueError("reply leaks a secret, blocking send")
    return reply
```

## Running it inside pydantic-evals

`.absent()` and `.expected()` turn a lexicon into an evaluator, for when you want the same check
running as part of a `Dataset` alongside everything else.

```py
from pydantic_evals import Case, Dataset

from lexguard import Servility, Slop


async def agent(prompt: str) -> str:
    return "Great question! Let us delve in. Hope this helps!"


dataset = Dataset(
    name="prose",
    cases=[Case(name="explainer", inputs="explain database indexing")],
    evaluators=[Slop.absent(), Servility.absent()],
)
report = dataset.evaluate_sync(agent)
print(sorted(name for name, result in report.cases[0].assertions.items() if not result.value))
#> ['no_postamble', 'no_slop', 'no_sycophancy']
```

## Failures tell you what to change

```py
from pydantic_evals import Case, Dataset

from lexguard import Slop


async def agent(prompt: str) -> str:
    return "Let us delve into the intricate tapestry of indexing."


report = Dataset(
    name="prose", cases=[Case(inputs="explain indexing")], evaluators=[Slop.absent()]
).evaluate_sync(agent)
print(report.cases[0].assertions["no_slop"].reason)
"""
3 slop matches: "delve", "intricate", "tapestry"
  delve -> Let us delve into the intricate tapestry of in…
  intricate -> Let us delve into the intricate tapestry of indexing.
fix: swap for a plain verb or noun, or add these to the sampler ban list
"""
```

## From the command line

Installing lexguard puts a `lexguard` command on your path (no extra dependencies). `draft` is the
on-ramp: pipe a raw list of terms — a brain-dump, a spreadsheet column, an agent's proposal — and it
prints a cleaned, sorted, ruff-formatted `Lexicon` binding ready to paste into a module. It is
`ruff format` for keyword lists.

```console
$ pbpaste | lexguard draft vague --fix "resolve the referent or ask one clarifying question"
Vague = Lexicon(
    name="vague",
    indicates=[
        "at some point",
        "circle back",
        "some stuff",
    ],
    fix="resolve the referent or ask one clarifying question",
)

$ lexguard draft house_style < brainstorm.txt >> mylexicons.py
```

`ls` lists the built-ins by group and `show` prints one as paste-able code, so you can fork or
extend a shipped lexicon:

```console
$ lexguard ls
response (20): Anthropomorphic, Apology, CitationMarker, ... Slop, Sycophancy, ...
$ lexguard show slop >> mylexicons.py
```

## Docs

- [Lexicons](docs/lexicons/index.md): every lexicon that ships in the box, generated from
  source, one page per group
- [Writing a lexicon](docs/writing-a-lexicon.md) for your own domain
- [Rules](docs/rules.md) and the `when` / `unless` guards
- [Agents](docs/agents.md) under test with pydantic-ai
- [Integrations](docs/integrations/index.md): pydantic-evals, DeepEval, Inspect AI, and the
  framework-agnostic `RuleSpec`, each with its own page

## Prior art

The slop word lists overlap heavily with
[slop-forensics](https://github.com/sam-paech/slop-forensics), which derives them statistically
rather than by hand. Point `Lexicon.extend()` at that list if you want the empirical version.
The abstain semantics, where a lexicon that does not apply records nothing rather than a free pass,
is the same idea as a Snorkel labelling function returning `None`.
