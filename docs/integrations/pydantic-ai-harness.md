# pydantic-ai-harness

`lexguard_guard` builds a [pydantic-ai-harness](https://pydantic.dev/docs/ai/harness/guardrails/)
guard from a `Lexicon`, checked against whatever value it's given. Whether it asserts presence or
absence is the lexicon's own `fail_when_neutral`, not a flag here — same rule as every other
integration.

```py
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from pydantic_ai_harness.guardrails import OutputBlocked, OutputGuardrail

from lexguard import Slop
from lexguard.integrations.guardrails.pydantic_ai import lexguard_guard

agent = Agent(
    TestModel(custom_output_text="Let us delve into the intricate tapestry of caching."),
    capabilities=[OutputGuardrail(guard=lexguard_guard(Slop))],
)
try:
    agent.run_sync("explain caching")
except OutputBlocked as blocked:
    print(blocked)
    """
    3 slop matches: "delve", "intricate", "tapestry"
      delve -> Let us delve into the intricate tapestry of ca…
      intricate -> Let us delve into the intricate tapestry of caching.
    fix: swap for a plain verb or noun, or add these to the sampler ban list
    """
```

The same callable shape works for `InputGuardrail` and the argument half of `ToolGuardrail` too —
pick whichever the check belongs to:

```py
from pydantic_ai_harness.guardrails import InputGuardrail

from lexguard import Confidential
from lexguard.integrations.guardrails.pydantic_ai import lexguard_guard

guardrail = InputGuardrail(guard=lexguard_guard(Confidential))
```

## Checking a bundle

A guard can only return one `allow`/`block`, unlike the eval-framework adapters, so a `Bundle`
here does combine into a single decision — pass `lexguard_guard` a `Bundle` and it blocks if any
member fires, listing every one that did in the block message so nothing is hidden.

```py
from lexguard.integrations.guardrails.pydantic_ai import lexguard_guard
from lexguard.suites import Bloat

guard = lexguard_guard(Bloat)
print(guard("caching skips repeated work").action)
#> allow
print(guard("let us delve into the intricate tapestry, but basically it is simple").action)
#> block
```

## Install

```bash
uv add "lexguard[pydantic-ai-harness]"
```

Only this integration needs it; importing `lexguard` itself does not.
