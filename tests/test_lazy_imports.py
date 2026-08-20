from __future__ import annotations

import builtins
import sys

import pytest

import lexguard

pytestmark = pytest.mark.unit


def test_generic_suite_is_reachable_off_the_package():
    assert lexguard.GENERIC == [*lexguard.PROSE, *lexguard.ADHERENCE]


def test_unknown_attribute_still_raises_attribute_error():
    with pytest.raises(AttributeError, match="no attribute 'NotARealName'"):
        lexguard.NotARealName


def _block_pydantic_evals(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delitem(sys.modules, "lexguard.rule", raising=False)
    monkeypatch.delitem(sys.modules, "pydantic_evals", raising=False)
    monkeypatch.delitem(sys.modules, "pydantic_evals.evaluators", raising=False)
    real_import = builtins.__import__

    def blocked(name: str, *args: object, **kwargs: object) -> object:
        if name.startswith("pydantic_evals"):
            raise ImportError("simulated: pydantic-evals not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)


def test_rule_gives_an_install_hint_without_pydantic_evals(monkeypatch: pytest.MonkeyPatch):
    _block_pydantic_evals(monkeypatch)
    with pytest.raises(ImportError, match=r"lexguard\.Rule needs pydantic-evals"):
        lexguard.Rule


def test_generic_gives_an_install_hint_without_pydantic_evals(monkeypatch: pytest.MonkeyPatch):
    _block_pydantic_evals(monkeypatch)
    with pytest.raises(ImportError, match=r"lexguard\.GENERIC needs pydantic-evals"):
        lexguard.GENERIC
