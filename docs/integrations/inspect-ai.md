# Inspect AI

`lexguard_scorer` wraps a single `Lexicon` as an Inspect AI `Scorer`, checked against the
completion. Whether it asserts presence or absence is the lexicon's own `fail_when_neutral` (see
[writing a lexicon](../writing-a-lexicon.md#fail_when_neutral-what-a-match-means)). Scores
`CORRECT` on a pass and `INCORRECT` otherwise, with the usual diagnosis as the explanation.

```py
import asyncio

from inspect_ai.model import ChatMessageUser, ModelOutput
from inspect_ai.scorer import Target
from inspect_ai.solver import TaskState

from lexguard import Slop
from lexguard.integrations.evals.inspect_ai import lexguard_scorer

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
score = lexguard_scorer(Slop)
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
`Task`: `Task(dataset=..., solver=..., scorer=lexguard_scorer(Slop))`. Score several lexicons by
passing several scorers — each stays its own `CORRECT`/`INCORRECT` result, none of them merge.

## Install

```bash
uv add "lexguard[inspect-ai]"
```
