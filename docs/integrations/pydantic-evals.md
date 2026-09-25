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

`LexguardEvaluator` reports which words matched beyond the pass/fail assertion, and optionally how
dense they are:

- `{Label}Indicated` / `{Label}RuledOut` **labels** — which words matched, comma-joined, split by
  which list they came from. Either is omitted when nothing from that side fired, so a clean case
  adds no extra labels.
- With `density=True`, one **score** per lexicon from `Lexicon.density()` (the fraction of words
  that are hits), oriented so higher always reads as better: `{Label}Density` for a lexicon you
  want present, `Not{Label}Density` (one minus the density) for one you want absent. Off by
  default, because backends such as Logfire render every score as a quality percentage, and a raw
  "0% slop" reads as a failure next to the pass rates.

```py
from pydantic_evals import Case, Dataset

from lexguard import Politeness, Slop
from lexguard.integrations.evals.pydantic_evals import LexguardEvaluator


async def agent(prompt: str) -> str:
    return "could you please fix the fucking bug"


report = Dataset(
    name="tone",
    cases=[Case(inputs="fix the bug")],
    evaluators=[LexguardEvaluator(Politeness | Slop, density=True)],
).evaluate_sync(agent)
case = report.cases[0]
print(case.labels["PolitenessIndicated"].value)
#> could you, please
print(case.labels["PolitenessRuledOut"].value)
#> fucking
print(case.scores["PolitenessDensity"].value)
#> 0.2857142857142857
print(case.scores["NotSlopDensity"].value)
#> 1.0
```

`case.assertions["Politeness"].value` is always exactly `True` or `False` — it can't say whether a
reply barely failed or is riddled with the problem. Two `Slop` hits in a three-sentence answer and
two in a five-page report both fail identically there, but their `NotSlopDensity` scores won't
match — the first is much lower. Turn density on once outputs get long enough that whether the
concept appears at all stops being the interesting question and how often it does becomes the one.

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

## Exporting to Logfire

Logfire's default scrubbing redacts anything matching `auth`, which catches the
`UnsourcedAuthority` label and turns its results into `[Scrubbed due to 'Auth']`. A scrubbing
callback can let that label through while still redacting a real credential alongside it:

```py
import logfire


def keep_unsourced_authority(match: logfire.ScrubMatch) -> object:
    # only the label itself is allowed through: if anything else in the string still matches a
    # scrubbing pattern once the label is removed, redact as usual
    found = match.pattern_match
    if found.re.search(found.string.replace("UnsourcedAuthority", "")) is None:
        return match.value
    return None


logfire.configure(
    send_to_logfire="if-token-present",
    scrubbing=logfire.ScrubbingOptions(callback=keep_unsourced_authority),
)
```

Each `LexguardEvaluator` and `Observe` result names its lexicons by label only, not their full
word lists, and is tagged with lexguard's version as its evaluator version, so a dashboard can tell
results from older word lists apart from current ones.

## Install

```bash
uv add "lexguard[pydantic-evals]"
```

Only this integration (`LexguardEvaluator`, `Observe`) and the suites built from it (`PROSE`,
`ADHERENCE`, `GENERIC`) need it; importing `lexguard` itself does not.
