# Agents

Nothing here is specific to pydantic-ai. A `Dataset` task is any callable, so the rule is checking
whatever your task returns. `TestModel` just makes the examples run without a key.

```py
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from pydantic_evals import Case, Dataset

from lexica import Bloat, Servility

agent = Agent(TestModel(custom_output_text="Great question! Let us delve in. Hope this helps!"))


async def task(prompt: str) -> str:
    return (await agent.run(prompt)).output


report = Dataset(
    name="prose",
    cases=[Case(name="explainer", inputs="explain database indexing")],
    evaluators=[Bloat.absent(), Servility.absent()],
).evaluate_sync(task)
print(sorted(name for name, result in report.cases[0].assertions.items() if not result.value))
# > ['no_postamble', 'no_slop', 'no_sycophancy']
```

The task unwraps `.output` because a rule stringifies whatever it is handed, and an
`AgentRunResult` repr would match on its own wrapper. The alternative is passing `agent.run`
straight in and putting `field="output"` on every rule.

## Structured output

`custom_output_args` builds the output tool call, so the agent does not retry against a text part
it cannot parse.

```py
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from pydantic_evals import Case, Dataset

from lexica import Confidential


class Ticket(BaseModel):
    summary: str
    internal_notes: str


agent = Agent(
    TestModel(
        custom_output_args={
            "summary": "Customer locked out of their account.",
            "internal_notes": "Their password is hunter2, reset it manually.",
        }
    ),
    output_type=Ticket,
)


async def task(prompt: str) -> Ticket:
    return (await agent.run(prompt)).output


report = Dataset(
    name="triage",
    cases=[Case(inputs="customer cannot log in")],
    evaluators=[Confidential.absent(field="internal_notes")],
).evaluate_sync(task)
print(report.cases[0].assertions["no_confidential"].reason)
"""
1 confidential match in internal_notes: "password"
  password -> Their password is hunter2, reset it manually.
fix: redact the secret before it is persisted or echoed; store a reference, never the value
"""
```

## Holding the agent still

`TestModel` returns one canned response regardless of the prompt. That is a feature when testing
guards, because it lets you vary only the request and see which rules arm.

```py
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from pydantic_evals import Case, Dataset

from lexica import Overclaim, UncertaintyAdmission

agent = Agent(TestModel(custom_output_text="This is guaranteed to work, it never fails."))


async def task(prompt: str) -> str:
    return (await agent.run(prompt)).output


report = Dataset(
    name="scoping",
    cases=[Case(inputs="will this migration work?")],
    evaluators=[Overclaim.absent(), UncertaintyAdmission.expected()],
).evaluate_sync(task)
print({name: result.value for name, result in report.cases[0].assertions.items()})
# > {'no_overclaim': False, 'has_uncertainty_admission': False}
```

## Alongside the built in evaluators

Rules are ordinary pydantic-evals evaluators, so they sit next to `MaxToolCalls`,
`ToolCorrectness`, `IsInstance` and the rest in the same list. Reach for those first for anything
structural. Lexicons are for what the text says.
