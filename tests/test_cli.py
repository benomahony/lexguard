from __future__ import annotations

import subprocess

import pytest

import lexguard
from lexguard import LEXICONS, Lexicon
from lexguard.cli import _picker, _slug, _symbol, main

pytestmark = pytest.mark.unit


def run_binding(out: str) -> object:
    namespace: dict[str, object] = {"Lexicon": Lexicon}
    exec(out, namespace)  # noqa: S102
    return namespace


def test_bare_command_lists_one_importable_symbol_per_line(capsys):
    # capsys makes stdout a non-tty, so the bare command prints the plain list
    assert main([]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == len(LEXICONS)
    assert "Slop" in lines
    for symbol in lines:
        assert hasattr(lexguard, symbol), symbol


def test_name_prints_a_built_in_that_round_trips(capsys):
    assert main(["Slop"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("Slop = Lexicon(")
    assert run_binding(out)["Slop"] == LEXICONS["slop"]


@pytest.mark.parametrize("query", ["due_date", "DueDate", "duedate"])
def test_name_resolves_both_snake_name_and_pascal_symbol(query, capsys):
    assert main([query]) == 0
    assert capsys.readouterr().out.startswith("DueDate = Lexicon(")


def test_unknown_name_is_an_error(capsys):
    assert main(["nope"]) == 2
    assert "no lexicon named" in capsys.readouterr().err


def test_picker_prefers_any_fzf_compatible_finder(monkeypatch):
    monkeypatch.delenv("LEXGUARD_PICKER", raising=False)
    monkeypatch.setattr("shutil.which", lambda tool: f"/usr/bin/{tool}" if tool == "sk" else None)
    assert _picker() == ["/usr/bin/sk", "--preview", "lexguard {}"]


def test_picker_honours_an_env_override(monkeypatch):
    monkeypatch.setenv("LEXGUARD_PICKER", "myfinder --preview 'lexguard {}'")
    assert _picker() == ["myfinder", "--preview", "lexguard {}"]


def test_picker_is_none_when_nothing_is_installed(monkeypatch):
    monkeypatch.delenv("LEXGUARD_PICKER", raising=False)
    monkeypatch.setattr("shutil.which", lambda _: None)
    assert _picker() is None


def test_interactive_bare_command_opens_the_picker(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setattr("lexguard.cli._picker", lambda: ["fzf", "--preview", "lexguard {}"])
    calls: dict[str, object] = {}

    def fake_run(cmd, **kwargs):
        calls["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="Slop\n", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    assert main([]) == 0
    assert calls["cmd"][0] == "fzf"
    assert capsys.readouterr().out.startswith("Slop = Lexicon(")


def test_cancelling_the_picker_exits_cleanly(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setattr("lexguard.cli._picker", lambda: ["fzf"])
    monkeypatch.setattr(
        "subprocess.run",
        lambda cmd, **kw: subprocess.CompletedProcess(cmd, 130, stdout="", stderr=""),
    )
    assert main([]) == 0
    assert capsys.readouterr().out == ""


def test_bare_command_lists_when_no_picker_even_if_interactive(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setattr("lexguard.cli._picker", lambda: None)
    assert main([]) == 0
    assert len(capsys.readouterr().out.splitlines()) == len(LEXICONS)


def test_slug_and_symbol_reconstruct_the_house_names():
    assert _slug("Format List") == "format_list"
    assert _symbol("format_list") == "FormatList"
    # _symbol(name) must reproduce the exact symbol the package exports each built-in under
    assert all(hasattr(lexguard, _symbol(name)) for name in LEXICONS)
