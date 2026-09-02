# pydantic-ai-harness

`lexguard_guard` builds a [pydantic-ai-harness](https://pydantic.dev/docs/ai/harness/guardrails/)
guard from a `Lexicon`, checked against whatever value it's given. Whether it asserts presence or
absence is the lexicon's own `fail_when_neutral`, not a flag here — same rule as every other
integration.

By default a failed verdict retries, handing the model the lexicon failure reason and another
attempt:

```py
from pydantic_ai import Agent, UnexpectedModelBehavior
from pydantic_ai.models.test import TestModel
from pydantic_ai_harness.guardrails import OutputGuardrail

from lexguard import Slop
from lexguard.integrations.guardrails.pydantic_ai import lexguard_guard

agent = Agent(
    TestModel(custom_output_text="Let us delve into the intricate tapestry of caching."),
    capabilities=[OutputGuardrail(guard=lexguard_guard(Slop))],
)
try:
    agent.run_sync("explain caching")
except UnexpectedModelBehavior as exceeded:
    print(exceeded)
    #> Exceeded maximum output retries (1)
```

Pass `on_fail="block"` to reject the value outright instead — the right call for an
`InputGuardrail`, where there's no model output to retry:

```py
from pydantic_ai_harness.guardrails import InputGuardrail

from lexguard import Confidential
from lexguard.integrations.guardrails.pydantic_ai import lexguard_guard

guardrail = InputGuardrail(guard=lexguard_guard(Confidential, on_fail="block"))
```

## Checking a bundle

A guard can only return one result, unlike the eval-framework adapters, so a `Bundle` here does
combine into a single decision — pass `lexguard_guard` a `Bundle` and it fails if any member
fires, listing every one that did in the message so nothing is hidden.

```py
from lexguard.integrations.guardrails.pydantic_ai import lexguard_guard
from lexguard.suites import Bloat

guard = lexguard_guard(Bloat)
print(guard("caching skips repeated work").action)
#> allow
print(guard("let us delve into the intricate tapestry, but basically it is simple").action)
#> retry
```

## Install

```bash
uv add "lexguard[pydantic-ai-harness]"
```

Only this integration needs it; importing `lexguard` itself does not.
