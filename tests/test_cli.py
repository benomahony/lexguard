from __future__ import annotations

import io

import pytest

import lexguard
from lexguard import LEXICONS, Lexicon
from lexguard.cli import _slug, _symbol, main

pytestmark = pytest.mark.unit


def feed(monkeypatch, text: str) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(text))


def run_binding(out: str) -> object:
    namespace: dict[str, object] = {"Lexicon": Lexicon}
    exec(out, namespace)  # noqa: S102
    return namespace


def test_draft_cleans_and_sorts_a_raw_blob(monkeypatch, capsys):
    feed(monkeypatch, "circle back\nat some point\nSome Stuff\ncircle back\n")
    assert main(["draft", "vague"]) == 0
    out = capsys.readouterr().out
    namespace = run_binding(out)
    lexicon = namespace["Vague"]
    assert isinstance(lexicon, Lexicon)
    assert lexicon.name == "vague"
    assert sorted(lexicon.indicates) == ["at some point", "circle back", "some stuff"]


def test_draft_splits_on_commas_and_newlines(monkeypatch, capsys):
    feed(monkeypatch, "a, b\nc")
    main(["draft", "x"])
    lexicon = run_binding(capsys.readouterr().out)["X"]
    assert sorted(lexicon.indicates) == ["a", "b", "c"]


def test_draft_carries_fix_and_rules_out(monkeypatch, capsys):
    feed(monkeypatch, "going forward\nutilise")
    main(["draft", "House Style", "--fix", "prefer the shorter word", "--rules-out", "on brand"])
    out = capsys.readouterr().out
    lexicon = run_binding(out)["HouseStyle"]
    assert lexicon.name == "house_style"
    assert lexicon.fix == "prefer the shorter word"
    assert "on brand" in lexicon.rules_out


def test_draft_import_flag_emits_the_import_line(monkeypatch, capsys):
    feed(monkeypatch, "utilise")
    main(["draft", "x", "--import"])
    out = capsys.readouterr().out
    assert out.startswith("from lexguard import Lexicon\n\n")


def test_draft_on_empty_stdin_is_an_error(monkeypatch, capsys):
    feed(monkeypatch, "   \n\n")
    assert main(["draft", "x"]) == 2
    assert "no terms" in capsys.readouterr().err


def test_ls_lists_every_group_with_importable_symbols(capsys):
    assert main(["ls"]) == 0
    out = capsys.readouterr().out
    assert "response (20):" in out
    assert "Slop" in out
    # every symbol ls prints must be importable from the package
    for symbol in out.replace(",", " ").split():
        if symbol[:1].isupper():
            assert hasattr(lexguard, symbol), symbol


def test_show_prints_a_built_in_that_round_trips(capsys):
    assert main(["show", "Slop"]) == 0  # case-insensitive
    out = capsys.readouterr().out
    assert out.startswith("Slop = Lexicon(")
    assert run_binding(out)["Slop"] == LEXICONS["slop"]


@pytest.mark.parametrize("query", ["due_date", "DueDate", "duedate"])
def test_show_resolves_both_snake_name_and_pascal_symbol(query, capsys):
    assert main(["show", query]) == 0
    assert capsys.readouterr().out.startswith("DueDate = Lexicon(")


def test_show_unknown_name_is_an_error(capsys):
    assert main(["show", "nope"]) == 2
    assert "no built-in lexicon" in capsys.readouterr().err


def test_no_subcommand_exits_nonzero():
    with pytest.raises(SystemExit) as exit_info:
        main([])
    assert exit_info.value.code != 0


def test_slug_and_symbol_reconstruct_the_house_names():
    assert _slug("Format List") == "format_list"
    assert _symbol("format_list") == "FormatList"
    # _symbol(name) must reproduce the exact symbol the package exports each built-in under
    assert all(hasattr(lexguard, _symbol(name)) for name in LEXICONS)
