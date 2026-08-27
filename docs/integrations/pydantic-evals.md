# pydantic-evals

`.absent()` and `.expected()` build a `Check` and wrap it in a pydantic-evals `Rule` in one
step, for use as an `Evaluator` in a `Dataset`. See [Rules](../rules.md) and
[Agents](../agents.md) for the guards and structured-output scoping this gives you.

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
`report.print(include_reasons=True)` renders the whole `Dataset` as a table.

## Install

```bash
uv add "lexguard[pydantic-evals]"
```

Only `Rule`, `Observe`, and the suites built from them (`PROSE`, `ADHERENCE`, `GENERIC`) need it;
importing `lexguard` itself does not.
