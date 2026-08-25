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

For which concepts have a research basis and where openly-licensed word lists exist to draw from,
see [Evidence behind the lexicons](evidence.md).

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

## Mutually-exclusive families

Pairing generalises. When a set of lexicons are **mutually exclusive** — a request has one format,
one priority, one deadline hardness — the clean design is a *full mirror*: every member rules out
every other member's indicators. Mixed wording then denies all of them, and a term added to one
member cancels the rest for free, so the lists cannot drift apart.

```py
from lexguard import HighPriority, LowPriority

print(HighPriority.signal("this is high priority, drop everything"))
#> present
print(LowPriority.signal("this is high priority, drop everything"))
#> denied
print(LowPriority.signal("low priority, no rush"))
#> present
print(HighPriority.signal("high priority but do it whenever"))
#> denied
```

Three things decide whether a family should be mirrored:

**Mutual exclusivity, not exhaustiveness.** You only need that no text is truly two of these at
once. You do *not* need them to cover the space: a medium-priority task hits no member and is
correctly `absent` on all of them. Opposites with a neutral middle are still a family.

**Faithful indicators.** A full mirror is only safe if every indicator is specific enough to also
be a safe *blocker* for its siblings — present only when its concept genuinely holds. A bare word
that is a genus shared with a sibling breaks this: `priority` is a substring of `low priority`, so
mirrored into the low-priority blockers it would deny "low priority" itself. The fix is to sharpen
the indicator (`high priority`), not to special-case the mirror. Mirroring is a forcing function
for indicator precision — the same lesson as [writing for precision](#write-for-precision-not-recall),
with teeth.

**Granularity.** Faithfulness has to hold at the granularity the matcher runs on: the whole text.
Hedging and overclaim are opposite *per claim*, but a paragraph holds many claims, so a hedge
about one point and a booster about another coexist without contradiction. They are not exclusive
at text granularity, so they are not a mirror family — they stay a hand-curated pair.

`tests/test_exclusive_families.py` declares the families and enforces the invariants: disjoint
indicators for every family, plus the full mirror for those marked `mirror=True`. Adding a term to
a mirrored member fails the suite until every sibling rules it out.

## Building on what ships

The built-ins are not a framework to subclass; they are source to copy. `lexguard slop` prints the
definition — paste it into your module, name it, and edit the list like any other code.

If you are genuinely composing at runtime — folding in an externally derived word list, say — build
a new lexicon from the parts:

```py
from lexguard import Lexicon, Slop

HouseSlop = Lexicon(
    name="house_slop",
    indicates=[*Slop.indicates, "going forward", "utilise"],
    rules_out=Slop.rules_out,
    fix="house style: prefer the shorter word",
)

print(len(Slop.indicates), len(HouseSlop.indicates))
#> 56 58
print(HouseSlop.signal("going forward we will utilise a new approach"))
#> present
print(Slop.signal("going forward we will utilise a new approach"))
#> absent
```

## Promote to code

A lexicon is a judgement artifact. It belongs in a module that is reviewed, diffed, tested, and
versioned — not round-tripped through JSON. When terms are curated at runtime (an agent proposing
additions in a self-improvement loop, say), they are transient data until a human commits them.
`as_code()` is that promotion step: it returns paste-able Python that reconstructs the lexicon.

```py
from lexguard import Lexicon

vague = Lexicon(name="vague", indicates=["circle back", "at some point"])

print(vague.as_code())
#> Lexicon(name='vague', indicates=['at some point', 'circle back'])
```

Terms are sorted, so re-emitting the same lexicon is byte-identical and a diff shows only the terms
that changed. The output is a compact expression; run it through your formatter to lay it out.

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
