from __future__ import annotations

import subprocess

import pytest

import lexguard
from lexguard import LEXICONS, Lexicon
from lexguard.cli import _binding, main

pytestmark = pytest.mark.unit


def test_bare_command_lists_every_lexicon_one_per_line(capsys):
    # capsys makes stdout a non-tty, so the bare command prints the plain list, not the picker
    assert main([]) == 0
    assert capsys.readouterr().out.splitlines() == sorted(LEXICONS)


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


def test_bare_command_launches_fzf_when_present_and_interactive(monkeypatch, capsys):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/fzf")
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    calls: dict[str, object] = {}

    def fake_run(cmd, **kwargs):
        calls["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="slop\n", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    assert main([]) == 0
    assert calls["cmd"] == ["/usr/bin/fzf", "--preview", "lexguard {}"]
    assert capsys.readouterr().out.startswith("Slop = ")


def test_cancelling_the_picker_exits_cleanly(monkeypatch, capsys):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/fzf")
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setattr(
        "subprocess.run",
        lambda cmd, **kw: subprocess.CompletedProcess(cmd, 130, stdout="", stderr=""),
    )
    assert main([]) == 0
    assert capsys.readouterr().out == ""


def test_no_fzf_falls_back_to_the_list_even_when_interactive(monkeypatch, capsys):
    monkeypatch.setattr("shutil.which", lambda _: None)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    assert main([]) == 0
    assert capsys.readouterr().out.splitlines() == sorted(LEXICONS)


def test_binding_reconstructs_every_export_symbol():
    assert _binding("due_date") == "DueDate"
    assert all(hasattr(lexguard, _binding(name)) for name in LEXICONS)
