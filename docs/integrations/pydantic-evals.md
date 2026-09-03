# pydantic-evals

`LexguardEvaluator` wraps a `Lexicon` as an `Evaluator` in one step, for use in a `Dataset`.
Whether it asserts presence or absence is the lexicon's own `fail_when_neutral`, not a flag here.
See [writing a lexicon](../writing-a-lexicon.md#fail_when_neutral-what-a-match-means) for the full
explanation.

```py
from pydantic_evals import Case, Dataset

from lexguard import Slop
from lexguard.integrations.evals.pydantic_evals import LexguardEvaluator


async def agent(prompt: str) -> str:
    return "Let us delve into the intricate tapestry of caching."


report = Dataset(
    name="prose",
    cases=[Case(name="explainer", inputs="explain caching")],
    evaluators=[LexguardEvaluator(Slop)],
).evaluate_sync(agent)
print(report.cases[0].assertions["Slop"].value)
#> False
print(report.cases[0].assertions["Slop"].reason)
"""
3 slop matches: "delve", "intricate", "tapestry"
  delve -> Let us delve into the intricate tapestry of ca…
  intricate -> Let us delve into the intricate tapestry of caching.
fix: swap for a plain verb or noun, or add these to the sampler ban list
"""
```

Pulling values out like that is only to keep this example's output checkable; day to day,
`report.print(include_reasons=True)` renders the whole `Dataset` as a table.

Each instance checks exactly one `Lexicon` — check several lexicons by listing several instances,
so a failure always points at exactly which one fired rather than an averaged or merged result:

```py
from pydantic_evals import Case, Dataset

from lexguard import Apology, Postamble, Preamble, Slop, Sycophancy
from lexguard.integrations.evals.pydantic_evals import LexguardEvaluator


async def agent(prompt: str) -> str:
    return "Great question! Let us delve in. Hope this helps!"


report = Dataset(
    name="prose",
    cases=[Case(inputs="explain database indexing")],
    evaluators=[
        LexguardEvaluator(Slop),
        LexguardEvaluator(Preamble),
        LexguardEvaluator(Postamble),
        LexguardEvaluator(Sycophancy),
        LexguardEvaluator(Apology),
    ],
).evaluate_sync(agent)
print(sorted(name for name, result in report.cases[0].assertions.items() if not result.value))
#> ['Postamble', 'Slop', 'Sycophancy']
```

## Which terms fired, and how dense

`LexguardEvaluator` reports two extra things per lexicon beyond the pass/fail assertion:

- `{Label}Indicated` / `{Label}RuledOut` **labels** — which words matched, comma-joined, split by
  which list they came from. Either is omitted when nothing from that side fired, so a clean case
  adds no extra labels.
- `{Label}IndicatedDensity` / `{Label}RuledOutDensity` **scores** — `Lexicon.density()`: the
  fraction of words that are hits, always in `[0, 1]`. Unlike the labels, these land in
  `case.scores`, pydantic-evals' real numeric-metric bucket, and are always present (0.0 on a
  clean case), so `report.averages()` gives a genuine per-dataset rate rather than a count you'd
  have to average yourself.

```py
from pydantic_evals import Case, Dataset

from lexguard import Politeness
from lexguard.integrations.evals.pydantic_evals import LexguardEvaluator


async def agent(prompt: str) -> str:
    return "could you please fix the fucking bug"


report = Dataset(
    name="tone",
    cases=[Case(inputs="fix the bug")],
    evaluators=[LexguardEvaluator(Politeness)],
).evaluate_sync(agent)
case = report.cases[0]
print(case.labels["PolitenessIndicated"].value)
#> could you, please
print(case.labels["PolitenessRuledOut"].value)
#> fucking
print(case.scores["PolitenessRuledOutDensity"].value)
#> 0.14285714285714285
```

`case.assertions["Politeness"].value` is always exactly `True` or `False` — it can't say whether a
reply barely failed or is riddled with the problem. Two `Slop` hits in a three-sentence answer and
two in a five-page report both fail identically there, but their `SlopIndicatedDensity` scores
won't match — the first is a much higher density. Lean on the scores once outputs get long enough
that whether the concept appears at all stops being the interesting question and how often it does
becomes the one.

## Wanting a concept present

`Confirmation` is built with `fail_when_neutral=True`, so `LexguardEvaluator(Confirmation)` fails
when the reply never actually confirms anything — hedging or silence both count as a fail, only a
genuine confirmation passes. See
[writing a lexicon](../writing-a-lexicon.md#fail_when_neutral-what-a-match-means) for the full
explanation.

```py
from pydantic_evals import Case, Dataset

from lexguard import Confirmation
from lexguard.integrations.evals.pydantic_evals import LexguardEvaluator


async def agent(prompt: str) -> str:
    return "Maybe, I'm not totally sure yet."


report = Dataset(
    name="decisiveness",
    cases=[Case(inputs="should we ship it?")],
    evaluators=[LexguardEvaluator(Confirmation)],
).evaluate_sync(agent)
print(report.cases[0].assertions["Confirmation"].value)
#> False
```

## Observing before enforcing

`Observe` emits a label rather than an assertion, so a lexicon can be measured on live traffic
before anyone decides it should fail a build.

```py
from pydantic_evals import Case, Dataset

from lexguard import Hedging
from lexguard.integrations.evals.pydantic_evals import Observe


async def agent(prompt: str) -> str:
    return "It might possibly work, though generally it depends."


report = Dataset(
    name="shadow", cases=[Case(inputs="will this work")], evaluators=[Observe(Hedging)]
).evaluate_sync(agent)
print(report.cases[0].labels["Hedging"].value)
#> present
print(report.cases[0].assertions)
#> {}
```

## Checking a single live reply

`Dataset` isn't only for a batch test file — `evaluate()` is async, so a request handler can run
the same check against one live reply without maintaining a `Case` list anywhere. Pass
`progress=False` to skip the progress bar meant for a terminal.

```py
import asyncio

from pydantic_evals import Case, Dataset

from lexguard import Slop
from lexguard.integrations.evals.pydantic_evals import LexguardEvaluator


async def check_reply(prompt: str, reply: str) -> bool:
    dataset = Dataset(
        name="live", cases=[Case(inputs=prompt)], evaluators=[LexguardEvaluator(Slop)]
    )

    async def task(text: str) -> str:
        return reply

    report = await dataset.evaluate(task, progress=False)
    return bool(report.cases[0].assertions["Slop"].value)


print(asyncio.run(check_reply("explain caching", "let us delve into the intricate tapestry")))
#> False
```

## Install

```bash
uv add "lexguard[pydantic-evals]"
```

Only this integration (`LexguardEvaluator`, `Observe`) and the suites built from it (`PROSE`,
`ADHERENCE`, `GENERIC`) need it; importing `lexguard` itself does not.
