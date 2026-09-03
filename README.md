<p align="center">
  <img src="https://raw.githubusercontent.com/benomahony/lexguard/main/docs/assets/lexguard.png" alt="lexguard" width="50%">
</p>

# Lexguard

## The problem

You're evaluating an AI agent's reply: polite or rude, confident or overclaiming, clean or full of
leaked secrets. The obvious move is to grep for a few words, and a single word list breaks fast: a
reply that says "could you please fix the fucking bug" contains "please" and swears in the same
breath. One list can't tell those apart — it either misses the swearing or scores the reply as polite.

Lexguard is still just word matching. The difference is a second list per concept: words that rule
it back out. A check returns whether the concept holds, is simply absent, or is present but denied
by the wording around it.

```py
from lexguard import Politeness

print(Politeness("could you send this over when you get a sec?"))
#> True
print(Politeness("send me the report"))
#> False
print(Politeness("could you please fix the fucking bug"))
#> False
```

The last two both fail, but for different reasons: the second reply never mentions politeness, the
third does and then undercuts it. `.verdict(text).reason` is how you tell those apart:

```py
from lexguard import Politeness

print(Politeness.verdict("could you please fix the fucking bug").reason)
"""
politeness wording present but denied by: "fucking"
fix: add a courteous phrase (please, thanks, could you) and don't undercut it with sarcasm or profanity
"""
```

## How it works

A `Lexicon` is a named set of words and phrases that signal a concept (`indicates`), the words that
rule it back out (`rules_out`), and a one-sentence remedy for a hit (`fix`). It's matched by plain
substring — no model in the loop, so a check is instant and deterministic. A set ships in the box
already, tuned for agent transcripts — slop, sycophancy, leaked secrets, overclaimed confidence,
politeness, and more; run `lexguard` to list every one. To extend one, edit its list: `lexguard
<name>` prints it as source to paste into your own module. See
[Writing a lexicon](docs/writing-a-lexicon.md).

A `Lexicon` is callable — `Politeness(text)` is shorthand for `Politeness.matches(text)`, itself
built on a three-valued `.signal()` (`present` / `absent` / `denied`), with `.denied()` alongside it
for the third case. Reach for those when you just want a plain value. `.verdict(text)` is the
richer pass/fail-plus-`.reason` built on top, and it's the same call every integration below wraps,
whether that's an eval framework or a guardrail.

## What a match means

Most lexicons are checked for absence — `Slop`, `Confidential`, `Rudeness` are things you don't
want, so a match is the failure. A few, like `Confirmation` and `Politeness`, are checked for
presence instead: they set `fail_when_neutral=True`, so silence is the failure.

| matched? | `fail_when_neutral=False` (default) | `fail_when_neutral=True` |
| --- | --- | --- |
| yes | ✘ FAIL — e.g. `Slop`, found | ✔ PASS — e.g. `Confirmation`, said |
| no | ✔ PASS — e.g. `Slop`, clean | ✘ FAIL — e.g. `Confirmation`, silent |

See [Writing a lexicon](docs/writing-a-lexicon.md#fail_when_neutral-what-a-match-means) for the
full explanation.

## Install

```bash
uv add lexguard
```

The core has no dependencies. Each [integration](docs/integrations/index.md) is its own extra:

```bash
uv add "lexguard[pydantic-evals]"
uv add "lexguard[deepeval]"
uv add "lexguard[inspect-ai]"
uv add "lexguard[pydantic-ai-harness]"
```

To use it as a dev tool without adding it to any particular project, install it as one:

```bash
uv tool install lexguard
```

## Using it without an evals framework

`.verdict()` is a plain call over a string — nothing here needs `Dataset`, `Case`, or
pydantic-evals in general, and you get the diagnostic reason for free:

```py
from lexguard import Confidential


def guard(reply: str) -> str:
    verdict = Confidential.verdict(reply)
    if not verdict.passed:
        raise ValueError(verdict.reason)
    return reply


print(guard("send it over, all good"))
#> send it over, all good
```

A reply that actually leaks something raises with the full diagnosis attached — see
[Failures tell you what to change](#failures-tell-you-what-to-change) below for what that
`reason` text looks like.

## Running it inside pydantic-evals

`LexguardEvaluator`, from `lexguard.integrations.evals.pydantic_evals`, wraps a lexicon as an
evaluator, for when you want the same check running as part of a `Dataset` alongside everything else.

```py
from pydantic_evals import Case, Dataset

from lexguard import Apology, Postamble, Preamble, Slop, Sycophancy
from lexguard.integrations.evals.pydantic_evals import LexguardEvaluator


async def agent(prompt: str) -> str:
    return "Great question! Let us delve in. Hope this helps!"


dataset = Dataset(
    name="prose",
    cases=[Case(name="explainer", inputs="explain database indexing")],
    evaluators=[
        LexguardEvaluator(Slop),
        LexguardEvaluator(Preamble),
        LexguardEvaluator(Postamble),
        LexguardEvaluator(Sycophancy),
        LexguardEvaluator(Apology),
    ],
)
report = dataset.evaluate_sync(agent)
print(sorted(name for name, result in report.cases[0].assertions.items() if not result.value))
#> ['Postamble', 'Slop', 'Sycophancy']
```

Each rule checks exactly one lexicon and reports under its own name — a failure always points at
exactly what fired.

## Running it as a guardrail

`lexguard_guard`, from `lexguard.integrations.guardrails.pydantic_ai`, wraps a lexicon (or a
`Bundle` of them) as a [pydantic-ai-harness](https://pydantic.dev/docs/ai/harness/guardrails/)
`InputGuardrail`/`OutputGuardrail`/`ToolGuardrail` guard. By default a failed verdict retries,
handing the model the failure reason and another attempt; pass `on_fail="block"` to reject the
value outright instead.

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

A guard can only return one result, so this is the one place a `Bundle` genuinely combines
several lexicons into a single decision — a failure still lists every one that fired.

## Failures tell you what to change

Every failing `Verdict` carries a `reason`, and every lexicon carries a `fix`. A `Dataset` report
surfaces the first; called directly, a lexicon hands you the second on its own — enough to feed
straight back into the agent for another turn instead of failing the whole run.

```py
from lexguard import Slop

report = Slop.verdict("Let us delve into the intricate tapestry of indexing.")
print(report.reason)
"""
3 slop matches: "delve", "intricate", "tapestry"
  delve -> Let us delve into the intricate tapestry of in…
  intricate -> Let us delve into the intricate tapestry of indexing.
fix: swap for a plain verb or noun, or add these to the sampler ban list
"""

print(f"{Slop.name}: {Slop.fix}" if Slop.matches("caching skips repeated work") else None)
#> None
```

`.hits()` splits what it found into `.indicated` and `.ruled_out`, so a `denied` verdict can say
what did the denying, not just that it happened:

```py
from lexguard import Politeness

hits = Politeness.hits("could you please fix the fucking bug")
print(sorted(hits.indicated), sorted(hits.ruled_out))
#> ['could you', 'please'] ['fucking']
print(Politeness.verdict("could you please fix the fucking bug").reason)
"""
politeness wording present but denied by: "fucking"
fix: add a courteous phrase (please, thanks, could you) and don't undercut it with sarcasm or profanity
"""
```

`.matches()` and `.verdict().passed` are both exactly `True`/`False` — one `Slop` hit in a
sentence and ten in a page fail identically. `.density()` gives the same `indicated`/`ruled_out`
split as a real rate — the fraction of words that are hits, always in `[0, 1]` — instead of a raw
count, so it stays comparable once text gets long enough that presence alone stops being the
interesting question:

```py
from lexguard import Slop

print(Slop.density("Let us delve into the intricate tapestry of caching.").indicated)
#> 0.3333333333333333
```

## From the command line

`lexguard` lists the built-in lexicons, one per line; `lexguard <name>` prints one as `Lexicon(...)`
source to paste into your code.

```bash
lexguard
```

You can pipe it to fzf (or another tool if installed) to get a fuzzy picker.

```console
lexguard | fzf --preview 'lexguard {}'
```

Or you can drop a shell function in your `~/.zshrc` so `lg` opens a fuzzy picker
with a formatted, syntax-highlighted preview (via [ruff](https://github.com/astral-sh/ruff) and
[bat](https://github.com/sharkdp/bat)):

```zsh
lg() {
  lexguard | fzf --ansi --preview 'lexguard {} | ruff format - | bat -l python --color=always --style=plain'
}
```

## Docs

- [Lexicons](docs/lexicons/index.md): every lexicon that ships in the box, generated from
  source, one page per group
- [Writing a lexicon](docs/writing-a-lexicon.md) for your own domain
- [Agents](docs/agents.md) under test with pydantic-ai
- [Integrations](docs/integrations/index.md): evals (pydantic-evals, DeepEval, Inspect AI) and
  guardrails (pydantic-ai-harness), each with its own page

## Prior art

The slop word lists overlap heavily with
[slop-forensics](https://github.com/sam-paech/slop-forensics), which derives them statistically
rather than by hand. Fold that list into a `Slop` copy in your own module if you want the empirical
version. The abstain semantics, where a lexicon that does not apply records nothing rather than a
free pass, is the same idea as a Snorkel labelling function returning `None`.
