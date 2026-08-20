# Integrations

`RuleSpec` is the framework-agnostic core behind every integration lexguard ships: the same
lexicons, guards, and diagnosis text, compiled once and handed to whichever eval framework a
project already uses. `Lexicon.spec()` / `Bundle.spec()` build one directly, with no framework
installed at all.

```py
from lexguard import Slop

verdicts = Slop.spec().check(
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

`check(output, inputs)` takes the same `wanted`, `when`, `unless`, `field`, and `of` as
`.absent()` / `.expected()`; see [Rules](rules.md). It returns `None` rather than a list when a
guard did not fire or the scoped field was empty — the same silence-is-not-a-failure rule as
everywhere else in lexguard, so every adapter below treats a skipped spec as a pass, not a fail.

## pydantic-evals

`.absent()` and `.expected()` build a `RuleSpec` and wrap it in a pydantic-evals `Rule` in one
step, for use as an `Evaluator` in a `Dataset`. See [Rules](rules.md) and [Agents](agents.md) for
the guards and structured-output scoping this gives you.

```py
from pydantic_evals import Case, Dataset

from lexguard import Slop


async def agent(prompt: str) -> str:
    return "Let us delve into the intricate tapestry of caching."


report = Dataset(
    name="prose",
    cases=[Case(name="explainer", inputs="explain caching")],
    evaluators=[Slop.absent()],
).evaluate_sync(agent)
print(report.cases[0].assertions["no_slop"].value)
#> False
print(report.cases[0].assertions["no_slop"].reason)
"""
3 slop matches: "delve", "intricate", "tapestry"
  delve -> Let us delve into the intricate tapestry of ca…
  intricate -> Let us delve into the intricate tapestry of caching.
fix: swap for a plain verb or noun, or add these to the sampler ban list
"""
```

Pulling values out like that is only to keep this example's output checkable; day to day,
`report.print(include_reasons=True)` renders the whole `Dataset` as a table (see
[examples/usage.py](../examples/usage.py)).

`pydantic-evals` is its own extra — `uv add "lexguard[pydantic-evals]"`. Only `Rule`, `Observe`,
and the suites built from them (`PROSE`, `ADHERENCE`, `GENERIC`) need it; importing `lexguard`
itself does not.

## DeepEval

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

## Inspect AI

`lexguard_scorer` wraps a `RuleSpec` as an Inspect AI `Scorer`, scoring `CORRECT` when every
lexicon in the spec holds and `INCORRECT` otherwise, with the usual diagnosis as the explanation.

```py
import asyncio

from inspect_ai.model import ChatMessageUser, ModelOutput
from inspect_ai.scorer import Target
from inspect_ai.solver import TaskState

from lexguard import Slop
from lexguard.integrations.inspect_ai import lexguard_scorer

state = TaskState(
    model="mockllm/model",
    sample_id=0,
    epoch=0,
    input="explain caching",
    messages=[ChatMessageUser(content="explain caching")],
    output=ModelOutput.from_content(
        model="mockllm", content="Let us delve into the intricate tapestry of caching."
    ),
)
score = lexguard_scorer(Slop.spec())
result = asyncio.run(score(state, Target("")))
print(result.value)
#> I
print(result.explanation)
"""
3 slop matches: "delve", "intricate", "tapestry"
  delve -> Let us delve into the intricate tapestry of ca…
  intricate -> Let us delve into the intricate tapestry of caching.
fix: swap for a plain verb or noun, or add these to the sampler ban list
"""
```

That direct call is only to show what the scorer returns; day to day it goes straight into a
`Task`: `Task(dataset=..., solver=..., scorer=lexguard_scorer(Slop.spec()))`.

## Install

Each integration is its own extra, so a project only pulls in the eval framework it actually uses:

```bash
uv add "lexguard[pydantic-evals]"
uv add "lexguard[deepeval]"
uv add "lexguard[inspect-ai]"
```

The core — `Lexicon`, `Bundle`, `.signal()` / `.fires()` / `.denied()`, and `.spec()` — needs none
of them.
