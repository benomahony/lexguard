<p align="center">
  <img src="docs/assets/lexguard.png" alt="lexguard" width="50%">
</p>

# Lexguard

## The problem

You're evaluating an AI agent. You want to know whether its reply is polite, or whether it
overclaimed, leaked something it shouldn't have, or buried the answer under sycophantic preamble.
The obvious move is to grep the output for a few words, and one list of words breaks fast: an agent
that writes "could you please fix the fucking bug" used the word "please" and swore in the same
breath. A single word list can't tell those two apart, so it either misses the problem or, worse,
scores a bad reply as fine.

Lexguard is still just word matching, it's not doing anything clever with the text. The difference
is a second list: words that rule the concept back out. Point it at a reply and get back one of
three answers: the concept is there, it's absent, or the wording rules it out.

```py
from lexguard import Politeness

print(Politeness.signal("could you send this over when you get a sec?"))
#> present
print(Politeness.signal("send me the report"))
#> absent
print(Politeness.signal("could you please fix the fucking bug"))
#> denied
```

`denied` is not the same as `absent`. A reply with no politeness words at all is merely unasked for.
This one has a politeness word, but the swearing cancels it out, so it's rated denied, not present.

## How it works

That three-way check is a `Lexicon`: a named set of words and phrases that signal a concept
(`indicates`), the words that rule it out (`rules_out`), and a plain sentence saying what to do
about a hit (`fix`). It's matched by plain substring, no model in the loop, so a check is instant
and gives the same verdict every time. A set of them ship in the box already, tuned for agent
transcripts: what a user asked for and what a model produced, from slop and sycophancy to leaked
secrets and overclaimed confidence, alongside politeness; run `lexguard` to list every one.
Extending a lexicon means editing its list; `lexguard <name>` prints one as source to paste into
your own module and change. See [Writing a lexicon](docs/writing-a-lexicon.md).

`.signal()`, `.fires()` and `.denied()` are plain functions over text: call them directly on
whatever an agent returned, in a guardrail before a reply goes out, an `assert` in a unit test, or a
filter in a log pipeline.

## Install

```bash
uv add lexguard
```

The core has no dependencies. `.spec()` compiles a lexicon into a framework-agnostic `RuleSpec`,
which `.absent()` / `.expected()` and the [integrations](docs/integrations/index.md) turn into an
evaluator for whichever eval framework you use; each is its own extra:

```bash
uv add "lexguard[pydantic-evals]"
uv add "lexguard[deepeval]"
uv add "lexguard[inspect-ai]"
```

If you want to use it as a dev tool and not worry about which repo you are in then install it as a tool:

```bash
uv tool install lexguard
```

## Using it without an evals framework

`signal()`, `fires()` and `denied()` are the whole API surface at this layer: plain calls over a
string. Nothing here needs `Dataset`, `Case`, or pydantic-evals in general, so a lexicon works just
as well as a guardrail before a response goes out, a plain `assert` in a unit test, or a filter in
a log pipeline.

```py
from lexguard import Confidential


def guard(reply: str) -> str:
    if Confidential.fires(reply):
        raise ValueError("reply leaks a secret, blocking send")
    return reply
```

## Running it inside pydantic-evals

`.absent()` and `.expected()` turn a lexicon into an evaluator, for when you want the same check
running as part of a `Dataset` alongside everything else.

```py
from pydantic_evals import Case, Dataset

from lexguard import Servility, Slop


async def agent(prompt: str) -> str:
    return "Great question! Let us delve in. Hope this helps!"


dataset = Dataset(
    name="prose",
    cases=[Case(name="explainer", inputs="explain database indexing")],
    evaluators=[Slop.absent(), Servility.absent()],
)
report = dataset.evaluate_sync(agent)
print(sorted(name for name, result in report.cases[0].assertions.items() if not result.value))
#> ['no_postamble', 'no_slop', 'no_sycophancy']
```

## Failures tell you what to change

```py
from pydantic_evals import Case, Dataset

from lexguard import Slop


async def agent(prompt: str) -> str:
    return "Let us delve into the intricate tapestry of indexing."


report = Dataset(
    name="prose", cases=[Case(inputs="explain indexing")], evaluators=[Slop.absent()]
).evaluate_sync(agent)
print(report.cases[0].assertions["no_slop"].reason)
"""
3 slop matches: "delve", "intricate", "tapestry"
  delve -> Let us delve into the intricate tapestry of in…
  intricate -> Let us delve into the intricate tapestry of indexing.
fix: swap for a plain verb or noun, or add these to the sampler ban list
"""
```

## Closing the loop

`fix` is not just for a test report. It works standing alone, so a guardrail in the agent loop
does not just block a bad reply, it can hand the agent something to retry with. `guidance()` is
that message: the lexicon name, then the fix, so it names what fired when handed back on its own.

```py
from lexguard import Slop


def guard(reply: str) -> str | None:
    return Slop.guidance() if Slop.fires(reply) else None


print(guard("let us delve into the intricate tapestry"))
#> slop: swap for a plain verb or noun, or add these to the sampler ban list
print(guard("caching skips repeated work"))
#> None
```

A non-`None` result is the next prompt: feed it back in and let the agent take another turn,
instead of failing the whole run.

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
- [Rules](docs/rules.md) and the `when` / `unless` guards
- [Agents](docs/agents.md) under test with pydantic-ai
- [Integrations](docs/integrations/index.md): pydantic-evals, DeepEval, Inspect AI, and the
  framework-agnostic `RuleSpec`, each with its own page

## Prior art

The slop word lists overlap heavily with
[slop-forensics](https://github.com/sam-paech/slop-forensics), which derives them statistically
rather than by hand. Fold that list into a `Slop` copy in your own module if you want the empirical
version. The abstain semantics, where a lexicon that does not apply records nothing rather than a
free pass, is the same idea as a Snorkel labelling function returning `None`.
