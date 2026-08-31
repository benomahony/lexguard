from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

SRC = Path(__file__).resolve().parent.parent / "src" / "lexguard"
FRAMEWORKS = ("pydantic_evals", "deepeval", "inspect_ai")

# the core is every module outside the integrations package: matching, checks, words, suites, cli
CORE = sorted(p for p in SRC.rglob("*.py") if "integrations" not in p.parts)


def _module_scope_imports(path: Path) -> set[str]:
    """Modules imported at module scope. Imports inside a def/class are deferred, so excluded —
    that is exactly how suites.py reaches the pydantic-evals integration without eager coupling."""
    tree = ast.parse(path.read_text())
    found: set[str] = set()

    def visit(body: list[ast.stmt]) -> None:
        for node in body:
            if isinstance(node, ast.Import):
                found.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                found.add(node.module or "")  # relative form, e.g. "integrations.pydantic_evals"
            elif isinstance(node, ast.If | ast.Try | ast.With):
                visit(node.body)
                visit(getattr(node, "orelse", []))
                visit(getattr(node, "finalbody", []))
                for handler in getattr(node, "handlers", []):
                    visit(handler.body)
            # a FunctionDef / AsyncFunctionDef / ClassDef body is not module scope: skip it

    visit(tree.body)
    return found


@pytest.mark.parametrize("path", CORE, ids=lambda p: str(p.relative_to(SRC)))
def test_core_never_imports_an_eval_framework(path: Path) -> None:
    imported = _module_scope_imports(path)
    leaked = {name for name in imported if name.split(".")[0] in FRAMEWORKS}
    assert not leaked, f"{path.name} imports an eval framework at module scope: {sorted(leaked)}"


@pytest.mark.parametrize("path", CORE, ids=lambda p: str(p.relative_to(SRC)))
def test_core_never_imports_the_integrations_package(path: Path) -> None:
    imported = _module_scope_imports(path)
    leaked = {name for name in imported if "integrations" in name.split(".")}
    assert not leaked, f"{path.name} eagerly imports lexguard.integrations: {sorted(leaked)}"


def test_the_check_helper_actually_sees_a_planted_violation(tmp_path: Path) -> None:
    # guard the guard: a module-scope framework import must be caught, an in-function one must not
    eager = tmp_path / "eager.py"
    eager.write_text("import pydantic_evals\n")
    assert "pydantic_evals" in _module_scope_imports(eager)
    lazy = tmp_path / "lazy.py"
    lazy.write_text("def f():\n    import pydantic_evals\n    return pydantic_evals\n")
    assert "pydantic_evals" not in _module_scope_imports(lazy)
