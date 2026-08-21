from __future__ import annotations

import ast
import shutil
import subprocess

import pytest
from hypothesis import given
from hypothesis import strategies as st

from lexguard import LEXICONS, Lexicon
from lexguard.lexicon import literal, tidy

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


@given(st.lists(terms, max_size=12), st.lists(terms, max_size=8), names, st.text(max_size=60))
def test_as_code_is_valid_python(indicates, rules_out, name, fix):
    ast.parse(build(indicates, rules_out, name, fix).as_code())


def test_constructor_rejects_a_bare_string_instead_of_exploding_it():
    # a str is a Collection[str] of characters; the constructor must reject it, not tidy "abc"
    # into {"a", "b", "c"}. Splitting raw text into terms is the CLI's job, at its boundary.
    with pytest.raises(AssertionError, match="list of terms"):
        Lexicon(name="x", indicates="circle back")
    with pytest.raises(AssertionError, match="list of terms"):
        Lexicon(name="x", indicates=["a"], rules_out="b")


def test_flat_definition_matches_the_house_style():
    lexicon = Lexicon(
        name="vague",
        indicates=["circle back", "at some point"],
        rules_out=["by friday"],
        fix="ask one clarifying question",
    )
    assert lexicon.as_code() == (
        "Lexicon(\n"
        '    name="vague",\n'
        "    indicates=[\n"
        '        "at some point",\n'
        '        "circle back",\n'
        "    ],\n"
        "    rules_out=[\n"
        '        "by friday",\n'
        "    ],\n"
        '    fix="ask one clarifying question",\n'
        ")"
    )


def test_empty_rules_out_and_fix_are_omitted():
    code = Lexicon(name="x", indicates=["a"]).as_code()
    assert "rules_out" not in code
    assert "fix" not in code


def test_terms_are_one_per_line_with_trailing_commas():
    code = Lexicon(name="x", indicates=["a", "b", "c"]).as_code()
    assert '        "a",\n        "b",\n        "c",\n' in code


def test_apostrophes_use_double_quotes_and_round_trip():
    lexicon = Lexicon(name="x", indicates=["what's next", "don't"])
    assert '"what\'s next"' in lexicon.as_code()
    assert eval(lexicon.as_code(), {"Lexicon": Lexicon}) == lexicon  # noqa: S307


def test_embedded_double_quote_falls_back_to_single_quotes():
    lexicon = Lexicon(name="x", indicates=['he said "hi"'])
    assert "'he said \"hi\"'" in lexicon.as_code()
    assert eval(lexicon.as_code(), {"Lexicon": Lexicon}) == lexicon  # noqa: S307


def test_long_fix_wraps_into_implicit_concatenation():
    fix = "end on the last substantive sentence " * 4
    code = Lexicon(name="x", indicates=["a"], fix=fix).as_code()
    assert "    fix=(\n" in code
    assert eval(code, {"Lexicon": Lexicon}).fix == fix.strip()  # noqa: S307
    assert all(len(line) <= 100 for line in code.splitlines())


def test_single_unsplittable_long_fix_stays_on_one_line():
    fix = "x" * 120
    code = Lexicon(name="x", indicates=["a"], fix=fix).as_code()
    assert "fix=(" not in code
    assert eval(code, {"Lexicon": Lexicon}).fix == fix  # noqa: S307


@pytest.mark.parametrize("lexicon", LEXICONS.values(), ids=LEXICONS.keys())
def test_every_shipped_lexicon_round_trips_and_is_stable(lexicon: Lexicon):
    code = lexicon.as_code()
    rebuilt = eval(code, {"Lexicon": Lexicon})  # noqa: S307
    assert rebuilt == lexicon
    assert rebuilt.as_code() == code
    assert all(len(line) <= 100 for line in code.splitlines())


def test_extend_can_rename_the_derived_lexicon():
    from lexguard import Slop

    derived = Slop.extend(indicates=["going forward"], name="house_slop")
    assert derived.name == "house_slop"
    assert "going forward" in derived.indicates


def test_derived_form_emits_the_delta_against_the_base():
    from lexguard import Slop

    derived = Slop.extend(indicates=["going forward", "utilise"], name="house_slop")
    code = derived.as_code(base="Slop")
    assert code == (
        "Slop.extend(\n"
        "    indicates=[\n"
        '        "going forward",\n'
        '        "utilise",\n'
        "    ],\n"
        '    name="house_slop",\n'
        ")"
    )
    assert eval(code, {"Slop": Slop}) == derived  # noqa: S307


def test_derived_form_carries_a_changed_fix_and_new_rules_out():
    from lexguard import Slop

    derived = Slop.extend(rules_out=["on brand"], fix="prefer the shorter word")
    code = derived.as_code(base="Slop")
    assert "rules_out=[" in code
    assert 'fix="prefer the shorter word"' in code
    assert "indicates" not in code  # nothing was added on that axis
    assert eval(code, {"Slop": Slop}) == derived  # noqa: S307


def test_derived_form_with_no_delta_is_a_bare_extend():
    from lexguard import Slop

    assert Slop.extend().as_code(base="Slop") == "Slop.extend()"


def test_base_on_a_non_derived_lexicon_is_an_error():
    with pytest.raises(ValueError, match="not built with .extend"):
        Lexicon(name="x", indicates=["a"]).as_code(base="X")


@given(st.text(max_size=40))
def test_literal_round_trips_and_prefers_double_quotes(text):
    assert eval(literal(text)) == text  # noqa: S307
    # single quotes only appear as the outer quote when they escape fewer inner quotes
    if text.count('"') <= text.count("'"):
        assert literal(text).startswith('"')


@pytest.mark.integration
@pytest.mark.skipif(shutil.which("ruff") is None, reason="ruff not on PATH")
def test_emitted_source_survives_ruff_format_unchanged(tmp_path):
    source = "from lexguard import Lexicon\n\n" + "\n\n".join(
        f"_{name} = {lexicon.as_code()}" for name, lexicon in LEXICONS.items()
    )
    path = tmp_path / "emitted.py"
    path.write_text(source + "\n")
    check = subprocess.run(
        ["ruff", "format", "--line-length", "100", "--check", str(path)],
        capture_output=True,
        text=True,
    )
    assert check.returncode == 0, check.stdout + check.stderr
    lint = subprocess.run(
        ["ruff", "check", "--select", "E,F,W,I,N", str(path)],
        capture_output=True,
        text=True,
    )
    assert lint.returncode == 0, lint.stdout + lint.stderr
