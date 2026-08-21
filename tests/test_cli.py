from __future__ import annotations

import pytest

import lexguard
from lexguard import LEXICONS, Lexicon
from lexguard.cli import _binding, main

pytestmark = pytest.mark.unit


def test_bare_command_lists_every_lexicon_one_per_line(capsys):
    assert main([]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines == sorted(LEXICONS)


def test_name_prints_a_binding_that_round_trips(capsys):
    assert main(["slop"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("Slop = ")
    namespace: dict[str, object] = {"Lexicon": Lexicon}
    exec(out, namespace)  # noqa: S102
    assert namespace["Slop"] == LEXICONS["slop"]


def test_name_is_case_insensitive(capsys):
    assert main(["SLOP"]) == 0
    assert capsys.readouterr().out.startswith("Slop = ")


def test_unknown_name_is_an_error(capsys):
    assert main(["nope"]) == 2
    assert "no lexicon named" in capsys.readouterr().err


def test_binding_reconstructs_every_export_symbol():
    # the "Name = ..." the CLI emits must match the symbol the package actually exports
    assert _binding("due_date") == "DueDate"
    assert all(hasattr(lexguard, _binding(name)) for name in LEXICONS)
