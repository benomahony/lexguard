# Writing a lexicon

A lexicon is data. Three lists and a sentence.

```py
from lexguard import Lexicon

Estimate = Lexicon(
    name="estimate",
    indicates=[
        "by end of sprint",
        "delivery date",
        "man days",
        "roughly a week",
        "should take",
        "story points",
        "two weeks",
        "will take",
    ],
    rules_out=["depends on", "hard to say", "no estimate", "we would need to spike"],
    fix="do not put a duration on unscoped work; describe the next slice instead",
)

print(Estimate.signal("that should take roughly a week"))
#> present
print(Estimate.signal("it depends on how many clients hold session state"))
#> denied
```

## Write for precision, not recall

A lexicon fires or it does not, so a false positive costs you trust in the whole suite while a miss
costs you one caught case. Prefer phrases over bare words when the bare word is ambiguous.
`"just"` appears in "just a simple drop in" and also in "just checking". `"plug and play"` does not.

```py
from lexguard import Lexicon

Loose = Lexicon(name="loose", indicates=["just", "simple"])
Tight = Lexicon(name="tight", indicates=["plug and play", "out of the box", "drop in"])

print(Loose.signal("just checking you got my last message"))
#> present
print(Tight.signal("just checking you got my last message"))
#> absent
```

## rules_out is where the judgement lives

Pair lexicons that describe opposite ends of the same axis and have each rule the other out. Mixed
wording then resolves to `denied` instead of firing both.

```py
from lexguard import HardDeadline, SoftDeadline

print(HardDeadline.signal("this must be in by friday"))
#> present
print(HardDeadline.signal("ideally by friday"))
#> denied
print(SoftDeadline.signal("ideally friday, but it is a hard deadline"))
#> denied
```

## Extending what ships

`extend()` returns a new lexicon and keeps the original intact, so house style sits on top of the
shared list rather than forking it.

```py
from lexguard import Slop

HouseStyle = Slop.extend(
    indicates=["at this moment in time", "going forward", "in order to", "utilise"],
    fix="house style: prefer the shorter word",
)

print(len(Slop.indicates), len(HouseStyle.indicates))
#> 50 54
print(HouseStyle.signal("going forward we will utilise a new approach"))
#> present
print(Slop.signal("going forward we will utilise a new approach"))
#> absent
```

## Learning from misses

`extend()` is also the primitive a self-improving agent uses to grow its own guard. Every phrase a
reviewer flags that the guard let through is folded back in, so the next draft is scored against a
lexicon that learned from the last one.

```py
from lexguard import Slop

guard = Slop
print(guard.fires("let us circle back"))
#> False

# a reviewer flags "circle back" as filler the shipped guard never knew
guard = guard.extend(indicates=["circle back", "move the needle"])
print(guard.fires("let us circle back"))
#> True
print(Slop.fires("let us circle back"))
#> False
```

[examples/self_improving.py](../examples/self_improving.py) runs the whole loop as a real
pydantic-ai agent that flags its own misses through a tool and writes the grown guard back out as a
`Slop.extend(...)` module — lexicons stay code, so the authored guard is an ordinary file the next
`agent.run(...)` imports. That is the runtime capability-creation pattern from
[pydantic-ai-harness](https://github.com/pydantic/pydantic-ai-harness), with a lexicon as the
capability the agent extends.

## Grouping

`|` builds a set that keeps its members, so you still get one assertion per lexicon rather than one
blurred verdict.

```py
from lexguard import Padding, Slop, TransitionSlop

Bloat = Slop | TransitionSlop | Padding
print(Bloat.signals("moreover, it is essentially a tapestry"))
"""
{'slop': <Signal.present: 'present'>, 'transition_slop': <Signal.present: 'present'>, 'padding': <Signal.present: 'present'>}
"""
```

## Inspecting

```py
from lexguard import GROUPS, Sycophancy

print(Sycophancy)
#> Lexicon(sycophancy, 17 indicators, 0 blockers)
print(Sycophancy.examples())
#> ['brilliant question', 'excellent point', 'excellent question', 'good catch']
print({name: len(group) for name, group in GROUPS.items()})
#> {'request': 37, 'instruction': 19, 'response': 20, 'domain': 15}
```
