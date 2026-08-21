from __future__ import annotations

import pytest

from lexguard import LEXICONS, Lexicon
from lexguard.cli import main

pytestmark = pytest.mark.unit


def test_bare_command_lists_every_lexicon_one_per_line(capsys):
    assert main([]) == 0
    assert capsys.readouterr().out.splitlines() == sorted(LEXICONS)


def test_name_prints_source_that_round_trips(capsys):
    assert main(["slop"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("Lexicon(")
    assert eval(out, {"Lexicon": Lexicon}) == LEXICONS["slop"]  # noqa: S307


def test_name_is_case_insensitive(capsys):
    assert main(["SLOP"]) == 0
    assert capsys.readouterr().out.startswith("Lexicon(")


def test_unknown_name_is_an_error(capsys):
    assert main(["nope"]) == 2
    assert "no lexicon named" in capsys.readouterr().err
