# Agents

Rules check a pydantic-ai `Agent`'s reply the same way they check any other text: a `Dataset` task
is any callable, so a rule just inspects whatever it returns — no pydantic-ai-specific plumbing on
lexguard's side. `TestModel` here just makes the examples run without a key.

```py
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from pydantic_evals import Case, Dataset

from lexguard import Apology, Postamble, Preamble, Slop, Sycophancy
from lexguard.integrations.evals.pydantic_evals import LexguardEvaluator

agent = Agent(TestModel(custom_output_text="Great question! Let us delve in. Hope this helps!"))


async def task(prompt: str) -> str:
    return (await agent.run(prompt)).output


report = Dataset(
    name="prose",
    cases=[Case(name="explainer", inputs="explain database indexing")],
    evaluators=[
        LexguardEvaluator(Slop),
        LexguardEvaluator(Preamble),
        LexguardEvaluator(Postamble),
        LexguardEvaluator(Sycophancy),
        LexguardEvaluator(Apology),
    ],
).evaluate_sync(task)
print(sorted(name for name, result in report.cases[0].assertions.items() if not result.value))
#> ['Postamble', 'Slop', 'Sycophancy']
```

The task unwraps `.output` because a rule stringifies whatever it is handed, and an
`AgentRunResult` repr would match on its own wrapper.

## Holding the agent still

`TestModel` returns one canned response regardless of the prompt, which is useful when you want
to vary only the request across cases and see which rules fire.

```py
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from pydantic_evals import Case, Dataset

from lexguard import Hedging, Overclaim
from lexguard.integrations.evals.pydantic_evals import LexguardEvaluator

agent = Agent(TestModel(custom_output_text="This is guaranteed to work, it never fails."))


async def task(prompt: str) -> str:
    return (await agent.run(prompt)).output


report = Dataset(
    name="scoping",
    cases=[Case(inputs="will this migration work?")],
    evaluators=[LexguardEvaluator(Overclaim), LexguardEvaluator(Hedging)],
).evaluate_sync(task)
print({name: result.value for name, result in report.cases[0].assertions.items()})
#> {'Overclaim': False, 'Hedging': True}
```

## Alongside the built in evaluators

Rules are ordinary pydantic-evals evaluators, so they sit next to `MaxToolCalls`,
`ToolCorrectness`, `IsInstance` and the rest in the same list. Reach for those first for anything
structural. Lexicons are for what the text says.
