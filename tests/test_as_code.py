from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from lexguard import LEXICONS, Lexicon
from lexguard.lexicon import tidy

pytestmark = pytest.mark.unit

terms = st.text(max_size=30)
names = st.text(min_size=1, max_size=20).filter(lambda word: word.strip())


def build(indicates, rules_out, name, fix) -> Lexicon:
    # the constructor forbids a phrase that both indicates and rules out, so drop the overlap
    indicated = tidy(indicates)
    rules_out = [word for word in rules_out if not (tidy([word]) & indicated)]
    return Lexicon(name=name, indicates=indicates, rules_out=rules_out, fix=fix)


@given(st.lists(terms, max_size=12), st.lists(terms, max_size=8), names, st.text(max_size=60))
def test_as_code_round_trips_through_eval(indicates, rules_out, name, fix):
    lexicon = build(indicates, rules_out, name, fix)
    rebuilt = eval(lexicon.as_code(), {"Lexicon": Lexicon})  # noqa: S307
    assert rebuilt == lexicon


@given(st.lists(terms, max_size=12), st.lists(terms, max_size=8), names, st.text(max_size=60))
def test_as_code_is_deterministic(indicates, rules_out, name, fix):
    lexicon = build(indicates, rules_out, name, fix)
    # same terms in a different input order must yield byte-identical source
    shuffled = build(list(reversed(indicates)), list(reversed(rules_out)), name, fix)
    assert lexicon.as_code() == shuffled.as_code()
    assert lexicon.as_code() == lexicon.as_code()


def test_constructor_rejects_a_bare_string_instead_of_exploding_it():
    # a str is a Collection[str] of characters; the constructor must reject it, not tidy "abc"
    # into {"a", "b", "c"}. Splitting raw text into terms is the CLI's job, at its boundary.
    with pytest.raises(TypeError, match="list of terms"):
        Lexicon(name="x", indicates="circle back")
    with pytest.raises(TypeError, match="list of terms"):
        Lexicon(name="x", indicates=["a"], rules_out="b")


def test_flat_definition_shape():
    lexicon = Lexicon(
        name="vague",
        indicates=["circle back", "at some point"],
        rules_out=["by friday"],
        fix="ask one clarifying question",
    )
    assert lexicon.as_code() == (
        "Lexicon(name='vague', indicates=['at some point', 'circle back'], "
        "rules_out=['by friday'], fix='ask one clarifying question')"
    )


def test_empty_rules_out_fix_and_evidence_are_omitted():
    code = Lexicon(name="x", indicates=["a"]).as_code()
    assert "rules_out" not in code
    assert "fix" not in code
    assert "evidence" not in code


def test_evidence_round_trips_but_is_ignored_by_equality():
    # as_code() dumps the full source, evidence included, and it round-trips; but evidence does
    # not change what a lexicon matches, so it is ignored by equality
    cited = Lexicon(name="x", indicates=["a"], evidence="Author 2013")
    plain = Lexicon(name="x", indicates=["a"])
    code = cited.as_code()
    assert "evidence='Author 2013'" in code
    assert eval(code, {"Lexicon": Lexicon}).evidence == "Author 2013"  # noqa: S307
    assert cited == plain
    assert cited.evidence == "Author 2013"


def test_evidence_whitespace_is_collapsed():
    assert Lexicon(name="x", indicates=["a"], evidence="line one\n   line two").evidence == (
        "line one line two"
    )


@pytest.mark.parametrize("lexicon", LEXICONS.values(), ids=LEXICONS.keys())
def test_every_shipped_lexicon_round_trips_and_is_stable(lexicon: Lexicon):
    code = lexicon.as_code()
    rebuilt = eval(code, {"Lexicon": Lexicon})  # noqa: S307
    assert rebuilt == lexicon
    assert rebuilt.as_code() == code
