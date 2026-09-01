from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

SRC = Path(__file__).resolve().parent.parent / "src" / "lexguard"
# the core must never reach for an eval framework or its adapters at module scope
FORBIDDEN = {"pydantic_evals", "deepeval", "inspect_ai", "integrations"}
CORE = sorted(p for p in SRC.rglob("*.py") if "integrations" not in p.parts)


def _top_level_imports(path: Path) -> set[str]:
    """Modules imported at the top level. An import inside a def is deferred and excluded — that is
    how suites.py reaches the pydantic-evals integration without coupling the core to it."""
    names: set[str] = set()
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module or "")
    return names


@pytest.mark.parametrize("path", CORE, ids=lambda p: str(p.relative_to(SRC)))
def test_core_never_couples_to_an_eval_framework(path: Path) -> None:
    leaked = {name for name in _top_level_imports(path) if FORBIDDEN & set(name.split("."))}
    assert not leaked, f"{path.name} couples the core to {sorted(leaked)} at module scope"


def test_the_guard_sees_eager_imports_but_not_deferred_ones(tmp_path: Path) -> None:
    (tmp_path / "eager.py").write_text("import pydantic_evals\n")
    assert "pydantic_evals" in _top_level_imports(tmp_path / "eager.py")
    (tmp_path / "lazy.py").write_text("def f():\n    import pydantic_evals\n")
    assert "pydantic_evals" not in _top_level_imports(tmp_path / "lazy.py")
