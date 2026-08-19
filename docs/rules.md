# Rules

A lexicon observes. A rule commits to a verdict. There are two, and two guards.

| rule | assertion | passes when |
| --- | --- | --- |
| `Lexicon.absent()` | `no_<name>` | nothing in the output matches |
| `Lexicon.expected()` | `has_<name>` | the output signal is `present` |

## Guards

A guard makes the rule conditional on the request. `when` runs the rule only if the request
lexicon fires. `unless` runs it only if it does not.

```py
from pydantic_evals import Case, Dataset

from lexica import AdviceDemand, Disclaimer, NoCaveats


async def agent(prompt: str) -> str:
    return "Probably, though you should consult a professional before relying on it."


report = Dataset(
    name="adherence",
    cases=[
        Case(
            name="opted_out", inputs="is this clause enforceable? no disclaimers, i know the risks"
        ),
        Case(name="definition", inputs="what is a tort"),
        Case(name="advice", inputs="should i sue my landlord over this clause"),
    ],
    evaluators=[Disclaimer.absent(when=NoCaveats), Disclaimer.absent(unless=AdviceDemand)],
).evaluate_sync(agent)

print({case.name: sorted(case.assertions) for case in report.cases})
"""
{
    "opted_out": ["no_disclaimer[unless advice_demand]", "no_disclaimer[when no_caveats]"],
    "definition": ["no_disclaimer[unless advice_demand]"],
    "advice": [],
}
"""
```

The agent said the same thing three times. Only the request changed.

`opted_out` breaks both rules: the user opted out of caveats and was not seeking advice.
`definition` breaks one, the reflex disclaimer on a factual question. `advice` records nothing,
because a warning is legitimate when someone is about to act.

## Silence is not a pass

A guard that does not fire skips. It does not record a passing assertion. Vacuous truth would
otherwise fill a dashboard with green from rules that never ran.

```py
from pydantic_evals import Case, Dataset

from lexica import CitationDemand, CitationMarker


async def agent(prompt: str) -> str:
    return "Subprime lending and securitisation both played a part."


evaluators = [CitationMarker.expected(when=CitationDemand)]
asked = Dataset(
    name="asked",
    cases=[Case(inputs="what caused the 2008 crash, with sources")],
    evaluators=evaluators,
).evaluate_sync(agent)
did_not = Dataset(
    name="did_not", cases=[Case(inputs="what caused the 2008 crash")], evaluators=evaluators
).evaluate_sync(agent)

print({name: result.value for name, result in asked.cases[0].assertions.items()})
#> {'has_citation_marker[when citation_demand]': False}
print(did_not.cases[0].assertions)
#> {}
```

## Scoping to a field

`field` takes a dotted path into a structured output. `[]` walks a list.

```py
from pydantic import BaseModel
from pydantic_evals import Case, Dataset

from lexica import Confidential, Overclaim


class Ticket(BaseModel):
    summary: str
    internal_notes: str
    next_steps: list


async def agent(prompt: str) -> Ticket:
    return Ticket(
        summary="Customer locked out of their account.",
        internal_notes="Their password is hunter2, reset it manually.",
        next_steps=["Trigger a reset", "This will definitely fix it, guaranteed"],
    )


report = Dataset(
    name="triage",
    cases=[Case(inputs="customer cannot log in")],
    evaluators=[
        Confidential.absent(field="internal_notes"),
        Confidential.absent(field="summary"),
        Overclaim.absent(field="next_steps[]"),
    ],
).evaluate_sync(agent)
print({name: result.value for name, result in report.cases[0].assertions.items()})
#> {'no_confidential': False, 'no_confidential_2': True, 'no_overclaim': False}
```

Two rules named `no_confidential` collapse to one key. Scope a lexicon to one field per suite, or the
narrower rule wins silently.

## Observing before enforcing

`Observe` emits labels rather than assertions, so a lexicon can be measured on live traffic before
anyone decides it should fail a build.

```py
from pydantic_evals import Case, Dataset

from lexica import Disclaimer, Hedging, Observe


async def agent(prompt: str) -> str:
    return "It might possibly work, though generally it depends."


report = Dataset(
    name="shadow",
    cases=[Case(inputs="will this work")],
    evaluators=[Observe([Hedging, Disclaimer])],
).evaluate_sync(agent)
print({name: label.value for name, label in report.cases[0].labels.items()})
#> {'hedging': 'present', 'disclaimer': 'absent'}
print(report.cases[0].assertions)
#> {}
```
