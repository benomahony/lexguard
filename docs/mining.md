# Mining a lexicon from traces

Writing a lexicon by hand is the right default: judgement is the point, and `rules_out` especially
is judgement. But when you already have a pile of labelled runs — success and failure OTel traces
from an agent in production or under eval — those traces can *suggest* the words and phrases worth
curating. `lexguard.mine` reads them and ranks the wording whose presence tracks failure.

Like the core, it has no third-party dependencies: OTLP is JSON and the statistics are stdlib
maths.

## Association, not causation

A mined phrase is a **marker**, not a cause. "sorry" does not *make* an agent fail; it is a symptom
of a run already going wrong. That is exactly what a lexicon wants — it detects, it does not
intervene — so association is the right target. The one place causal thinking earns its keep is
guarding against **confounded** suggestions that will not generalise (see
[Adjusting for confounders](#adjusting-for-confounders)). The output is a starting point for
curation, never a finished lexicon.

## From traces to candidates

Point `extract_traces` at an OTLP export and `mine` at the result. The label is any function from a
trace to an outcome; `from_attribute` reads a verdict a judge or eval run already wrote onto the
span.

```py
from lexguard.mine import extract_traces, from_attribute, mine

fail = [
    "sorry, i'm not sure this is right",
    "apologies, i cannot be certain here",
    "sorry, maybe this could possibly work",
]
ok = [
    "run the migration then restart the worker",
    "set the timeout to thirty seconds",
    "delete the cache and redeploy the service",
]


def span(tid: str, answer: str, passed: bool) -> dict:
    return {
        "traceId": tid,
        "attributes": [{"key": "eval.passed", "value": {"boolValue": passed}}],
        "events": [
            {
                "name": "gen_ai.user.message",
                "attributes": [{"key": "content", "value": {"stringValue": "how do I fix it"}}],
            },
            {
                "name": "gen_ai.choice",
                "attributes": [{"key": "content", "value": {"stringValue": answer}}],
            },
        ],
    }


spans = []
for i in range(30):
    spans.append(span(f"f{i}", fail[i % 3], False))
    spans.append(span(f"p{i}", ok[i % 3], True))

traces = extract_traces({"resourceSpans": [{"scopeSpans": [{"spans": spans}]}]})
suggestions = mine(traces, label=from_attribute("eval.passed"))

print(suggestions)
#> Suggestions(group='response', n=60, base_rate=0.50, 13 indicates, 12 rules_out)
print([c.phrase for c in suggestions.indicates[:5]])
#> ['sorry', 'apologies', 'cannot', 'certain', 'here']
print([c.phrase for c in suggestions.rules_out[:5]])
#> ['cache', 'delete', 'migration', 'redeploy', 'restart']
```

The `indicates` list is failure-leaning wording; `rules_out` is wording that co-occurs with the
concept but lands in successes. Both lists carry noise (`here`, `cannot`) alongside the real signal
(`sorry`, `apologies`) — that is what the curator prunes. Bare function words are dropped
automatically as single-word candidates; a phrase like `"i'm not"` still stands. Each `Candidate`
also carries `odds_ratio`, `z`, `q` (its false-discovery rate), `support`, and example `snippet`s
so you can judge it.

## The signal is any callable

`mine` only needs a `Trace -> outcome` function, so an existing LLM judge drops straight in. Any of
`True`/`False`, `"pass"`/`"fail"`, `1`/`0`, or a `Label` works as the return; `None` abstains and
drops the trace, the same way a lexicon records nothing when it does not apply.

```py
from lexguard.mine import Message, Trace, normalize


def judge(trace: Trace) -> str:
    answer = trace.text("response")
    # swap this body for a call to your own LLM judge
    return "failure" if "sorry" in answer else "success"


good = Trace("1", (Message("assistant", "the timeout is 30s", "response"),))
bad = Trace("2", (Message("assistant", "sorry, i cannot tell", "response"),))
print(normalize(judge(good)))
#> success
print(normalize(judge(bad)))
#> failure
```

Pass it as `mine(traces, label=judge)`. Use `from_attribute("eval.passed")` instead when the
verdict is already stored on the trace, so you are not re-running a judge you have already paid for.

## Adjusting for confounders

Raw counts are a trap. If a hard task both fails more and uses distinctive vocabulary, that
vocabulary will look like a failure signal when it only marks the task. Name the confounding trace
attributes and `mine` stratifies on them (a Mantel-Haenszel adjusted odds ratio), so a phrase that
only survives by riding the confound drops out. The synthetic name `"length"` stratifies on answer
length, which otherwise makes every word in longer, failing answers look predictive.

```py
from lexguard.mine import Message, Trace, from_attribute, mine


def resp(tid: str, text: str, passed: bool, task: str) -> Trace:
    return Trace(
        tid, (Message("assistant", text, "response"),), {"eval.passed": passed, "task": task}
    )


traces = []
for i in range(24):
    traces.append(resp(f"e{i}", "apply the patch and rerun", True, "easy"))
for i in range(3):
    traces.append(resp(f"ef{i}", "apply the patch and rerun sorry", False, "easy"))
for i in range(9):
    traces.append(resp(f"hw{i}", "configure the widget then deploy", True, "hard"))
for i in range(9):
    traces.append(resp(f"hn{i}", "configure then deploy", True, "hard"))
for i in range(11):
    traces.append(resp(f"fw{i}", "configure the widget then deploy sorry", False, "hard"))
for i in range(11):
    traces.append(resp(f"fn{i}", "configure then deploy sorry", False, "hard"))

crude = mine(traces, label=from_attribute("eval.passed"), min_support=5)
adjusted = mine(traces, label=from_attribute("eval.passed"), confounders=("task",), min_support=5)

print([c.phrase for c in crude.indicates])
#> ['sorry', 'configure', 'deploy', 'widget']
print([c.phrase for c in adjusted.indicates])
#> ['sorry']
```

`widget`, `configure`, and `deploy` only look predictive because they cluster in the harder task.
Stratifying on `task` leaves `sorry`, the marker that holds within both strata.

## Curate, then validate

`suggest()` assembles the top candidates into a `Lexicon` — to hand-edit, not to ship. Mining and
checking on the same traces just measures memorisation, so split them: mine on one half and
`evaluate` on the other to see whether the wording generalises.

```py
from lexguard import Lexicon
from lexguard.mine import Message, Trace, evaluate, from_attribute

lexicon = Lexicon(name="apology", indicates=["sorry", "apologies"])
held_out = [
    Trace("a", (Message("assistant", "sorry about that", "response"),), {"eval.passed": False}),
    Trace("b", (Message("assistant", "the fix is one line", "response"),), {"eval.passed": True}),
    Trace("c", (Message("assistant", "deploy at noon", "response"),), {"eval.passed": True}),
]

print(evaluate(lexicon, held_out, label=from_attribute("eval.passed")))
#> Scorecard(precision=1.0, recall=1.0, f1=1.0, support=1, n=3)
```

## Roles map to groups

`extract_traces` tags each message with the lexguard [group](lexicons/index.md) that reads that
role: a system prompt is an `instruction`, the user turn is the `request`, the model turn is the
`response`, a tool result is `domain`. Mine one group at a time with `mine(..., group=...)`
(default `"response"`), so a phrase you mine from user requests lands where the request lexicons
already look.
