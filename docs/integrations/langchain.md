# LangChain

`lexguard_middleware` builds a [LangChain agent middleware](https://docs.langchain.com/oss/python/langchain/middleware/custom)
that checks a message against a `Lexicon` (or a `Bundle` of them) as it flows through a
`create_agent` agent. Whether it asserts presence or absence is the lexicon's own
`fail_when_neutral`, not a flag here — same rule as every other integration.

`on` picks the hook, mirroring pydantic-ai's input/output guardrail split: `on="output"` (the
default) runs `after_model` against the model's reply, `on="input"` runs `before_model` against
the incoming message.

By default a failed output hands the model the lexicon reason and loops back for another attempt,
up to `retries` times (default 1); once the budget is spent it raises `LexguardBlockedError`:

```py
from langchain.agents import create_agent
from langchain_core.language_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage

from lexguard import Slop
from lexguard.integrations.guardrails.langchain import lexguard_middleware

model = FakeMessagesListChatModel(
    responses=[
        AIMessage("Let us delve into the intricate tapestry of caching."),
        AIMessage("Caching skips repeated work."),
    ]
)
agent = create_agent(model=model, tools=[], middleware=[lexguard_middleware(Slop)])

out = agent.invoke({"messages": [HumanMessage("explain caching")]})
print(out["messages"][-1].text)
#> Caching skips repeated work.
```

The first reply is slop, so the middleware bounces it back to the model with the diagnosis; the
second is clean and passes. (A real model would generate the replies — the fake one just makes the
example deterministic.)

## Blocking instead of retrying

Pass `on_fail="block"` to reject the value outright — the middleware raises `LexguardBlockedError`
with the same reason on the first failure, no retry:

```py
from langchain.agents import create_agent
from langchain_core.language_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage

from lexguard import Slop
from lexguard.integrations.guardrails.langchain import (
    LexguardBlockedError,
    lexguard_middleware,
)

model = FakeMessagesListChatModel(responses=[AIMessage("let us delve into the tapestry")])
agent = create_agent(model=model, tools=[], middleware=[lexguard_middleware(Slop, on_fail="block")])
try:
    agent.invoke({"messages": [HumanMessage("explain caching")]})
except LexguardBlockedError as blocked:
    print(str(blocked).splitlines()[0])
    #> 2 slop matches: "delve", "tapestry"
```

There's nothing to retry on the input side, so an input guard must block — `on="input"` requires
`on_fail="block"`:

```py
from lexguard import Confidential
from lexguard.integrations.guardrails.langchain import lexguard_middleware

guard = lexguard_middleware(Confidential, on="input", on_fail="block")
```

## Checking a bundle

A hook resolves to one action, so — like the other guardrail adapter and unlike the eval ones — a
`Bundle` here combines into a single decision. Pass `lexguard_middleware` a `Bundle` and it fails
if any member fires, listing every one that did so nothing is hidden:

```py
from langchain.agents import create_agent
from langchain_core.language_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage

from lexguard.integrations.guardrails.langchain import (
    LexguardBlockedError,
    lexguard_middleware,
)
from lexguard.suites import Bloat

model = FakeMessagesListChatModel(
    responses=[AIMessage("let us delve in, but basically it is simple")]
)
agent = create_agent(
    model=model, tools=[], middleware=[lexguard_middleware(Bloat, on_fail="block")]
)
try:
    agent.invoke({"messages": [HumanMessage("explain caching")]})
except LexguardBlockedError as blocked:
    print("slop" in str(blocked), "padding" in str(blocked))
    #> True True
```

## Install

```bash
uv add "lexguard[langchain]"
```

Only this integration needs it; importing `lexguard` itself does not.
