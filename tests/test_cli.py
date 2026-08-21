from __future__ import annotations

import pytest

import lexguard
from lexguard import LEXICONS, Lexicon
from lexguard.cli import _slug, _symbol, main

pytestmark = pytest.mark.unit


def run_binding(out: str) -> object:
    namespace: dict[str, object] = {"Lexicon": Lexicon}
    exec(out, namespace)  # noqa: S102
    return namespace


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
