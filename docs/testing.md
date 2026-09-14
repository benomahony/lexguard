# Testing a lexicon

A lexicon [lives or dies on precision](writing-a-lexicon.md#write-for-precision-not-recall): a
false positive costs you trust in the whole suite, a miss costs you one caught case. The way you
hold a lexicon to that standard is examples. `expect` is a small DSL for writing them down: one
chain that says which texts should fire, which should stay silent, and which should be worded but
ruled back out, all checked in a single call.

```py
from lexguard import Politeness
from lexguard.testing import expect

expect(Politeness).present("could you send this over when you get a sec?").absent(
    "send me the report"
).denied("could you please fix the fucking bug").check()
```

`.check()` returns nothing when every example behaves, and raises the moment one does not, so it
drops straight into a pytest test, a doctest, or a `__main__` block. Nothing runs until you call
it: the chain is a declaration, and it is checked in one go.

## The three signals, spelled out

The verbs mirror `signal()`'s three values, so a chain reads as the behaviour you want:

- `.present(...)`: the concept fires cleanly.
- `.denied(...)`: the concept is worded, then ruled back out.
- `.absent(...)`: the concept is never mentioned.

That makes a [mirrored family](writing-a-lexicon.md#mutually-exclusive-families) something you can
pin down in place: each member fires on its own wording and is denied by its sibling's.

```py
from lexguard import HardDeadline, SoftDeadline
from lexguard.testing import expect

expect(HardDeadline).present("this must be in by friday").denied("ideally by friday").check()
expect(SoftDeadline).present("ideally friday").denied("hard deadline: friday").check()
```

## Presence or absence, whichever the lexicon means

Signals are the raw call. `.passes(...)` and `.fails(...)` test the
[`verdict`](writing-a-lexicon.md#fail_when_neutral-what-a-match-means) instead, so you assert the
pass or fail a check actually makes without tracking which way `fail_when_neutral` points.
`Politeness` wants to see courtesy, so silence fails it:

```py
from lexguard import Politeness
from lexguard.testing import expect

expect(Politeness).passes("thanks, could you take a look").fails("send me the report").check()
```

## When one breaks

`.report()` runs the same checks without raising and hands back what it found, ready to inspect:

```py
from lexguard import Slop
from lexguard.testing import expect

report = expect(Slop).absent("let us delve into the tapestry").report()
print(report.ok)
#> False
print(report)
"""
slop: 1 of 1 expectations failed
  want absent, got present: 'let us delve into the tapestry'
"""
```

`.check()` is `.report()` with a raise on top: the same text, as an `AssertionError`, naming every
case that broke and the outcome it got instead. A failure points at exactly the text and the
wording that moved it.

## In your suite

`expect` is part of the core, with no framework in the loop, so a lexicon you wrote for your own
domain is tested the same way the built-ins are.

```py
from lexguard import Sycophancy
from lexguard.testing import expect


def test_sycophancy_catches_flattery():
    expect(Sycophancy).present("great question, you're absolutely right").absent(
        "the index halves lookups"
    ).check()
```
