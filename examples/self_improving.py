"""A self-improving agent that grows its own lexicon.

An agent that gates its own prose can only catch the slop its lexicon already
knows. Every miss a reviewer spots is a word the guard *should* have held. This
is the whole self-improvement loop:

    draft -> score against the current lexicon -> fold each miss back in

`Lexicon.extend()` returns a lexicon of the same name carrying the new words, so
the next draft is measured against a guard that learned from the last one. The
learning runs in two directions: new `indicates` close a gap the guard missed,
and new `rules_out` retire a false alarm the guard raised on innocent wording.

Nothing here needs an evals framework or an API key. The agent is a canned list
of drafts (the way `TestModel` stands in for a real model elsewhere in these
examples) so the loop is deterministic and the lexicon is the only thing that
moves.
"""

from __future__ import annotations

from lexguard import Lexicon, Slop

# What the agent wrote over one review cycle. The first two drafts lean on filler
# the shipped lexicon has never seen; the third is what the loop is teaching it to
# write. "harness" is real slop, but "test harness" is a legitimate use of the
# word — the guard has to learn the difference rather than just banning more.
DRAFTS = [
    "We leverage a robust platform to circle back on quarterly synergy.",
    "This release lets teams double-click on the north star and move the needle.",
    "Faster imports, clearer errors, and a green test harness after the cache fix.",
]

# A reviewer's notes for each draft: filler the guard let through (folded into
# `indicates`), and any innocent wording it wrongly flagged (folded into
# `rules_out`). In a live system these come from thumbs-down feedback or a second
# model grading the first; here they are written down so the example is stable.
MISSED_SLOP = {
    0: ["circle back"],
    1: ["double-click", "north star", "move the needle"],
    2: [],
}
FALSE_ALARMS = {
    0: [],
    1: [],
    2: ["test harness"],
}


def catch_up(guard: Lexicon, draft: str, missed: list[str], excused: list[str]) -> Lexicon:
    """Score one draft, then hand back a lexicon that learned from its misses."""
    caught = sorted(guard.hits(draft))
    slipped = [phrase for phrase in missed if not guard.fires(phrase)]
    print(f"  draft:   {draft}")
    print(f"  caught:  {caught or '(nothing)'}")
    print(f"  missed:  {slipped or '(nothing)'}")
    print(f"  excused: {excused or '(nothing)'}")

    grown = guard.extend(indicates=slipped, rules_out=excused)
    # extend() keeps the identity and only ever adds to what the guard knew.
    assert grown.name == guard.name
    assert all(word in grown.indicates for word in guard.indicates)
    assert all(phrase in grown.indicates for phrase in slipped)
    assert all(phrase in grown.rules_out for phrase in excused)
    return grown


def review_cycle() -> Lexicon:
    guard = Slop  # start from exactly what shipped in the box
    started_with = len(guard.indicates)

    for i, draft in enumerate(DRAFTS):
        print(f"iteration {i}: guard knows {len(guard.indicates)} indicators")
        guard = catch_up(guard, draft, MISSED_SLOP[i], FALSE_ALARMS[i])
        print()

    print(f"grew from {started_with} to {len(guard.indicates)} indicators\n")
    assert len(guard.indicates) > started_with
    return guard


def proof(guard: Lexicon) -> None:
    """The point of the loop: what slipped through draft 0 is now caught."""
    print("re-scoring the first draft against the lexicon it trained:")
    print(f"  hits: {sorted(guard.hits(DRAFTS[0]))}")
    assert guard.fires("let us circle back on this")
    assert not Slop.fires("let us circle back on this"), "the shipped guard never knew this"

    # And the false alarm the reviewer excused stays quiet, while the bare word
    # it was carved out of still fires.
    assert guard.signal("we finally have a green test harness").name == "denied"
    assert guard.fires("harness the platform"), "only 'test harness' was excused, not 'harness'"
    print("  'circle back' now fires; 'test harness' is excused but 'harness' still fires")


if __name__ == "__main__":
    grown = review_cycle()
    proof(grown)
