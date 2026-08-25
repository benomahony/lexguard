"""Jinja macros loaded by zensical's macros plugin, for docs/lexicons/*.md and docs/index.md.

Registers functions that pull straight from the live registry (`lexguard.words`,
`lexguard.suites`) at build time, so a page can never carry a hand-typed or pre-generated
copy of a word list that drifts from the code, plus a macro that reuses README.md as the
site homepage without hand-duplicating its prose.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from lexguard import suites
from lexguard.lexicon import Bundle, Lexicon
from lexguard.words import MODULES

BUNDLES = {
    "Bloat": suites.Bloat,
    "Servility": suites.Servility,
    "Leakage": suites.Leakage,
    "Overreach": suites.Overreach,
}

README_PATH = Path(__file__).resolve().parent.parent / "README.md"


def _entries(group: str) -> list[tuple[str, Lexicon]]:
    module = MODULES[group]
    result = [(name, value) for name, value in vars(module).items() if isinstance(value, Lexicon)]
    assert result, f"{group} exports no lexicons"
    assert all(isinstance(value, Lexicon) for _, value in result)
    return sorted(result, key=lambda entry: entry[0])


def _field_rows(lexicon: Lexicon) -> list[str]:
    rows = [f"| indicates | {', '.join(sorted(lexicon.indicates))} |"]
    if lexicon.rules_out:
        rows.append(f"| rules out | {', '.join(sorted(lexicon.rules_out))} |")
    if lexicon.fix:
        rows.append(f"| fix | {lexicon.fix} |")
    if lexicon.source:
        rows.append(f"| source | {lexicon.source} |")
    assert rows, "a lexicon always indicates something"
    assert all(row.startswith("| ") and row.endswith(" |") for row in rows)
    return rows


def _lexicon_block(class_name: str, lexicon: Lexicon) -> str:
    header = ["| property | value |", "| --- | --- |"]
    lines = [f"#### `{class_name}`", "", *header, *_field_rows(lexicon)]
    result = "\n".join(lines)
    assert result.startswith(f"#### `{class_name}`")
    assert len(lines) >= len(header) + 2
    return result


def lexicon_table(group: str) -> str:
    assert group in MODULES, f"unknown lexicon group: {group}"
    blocks = [_lexicon_block(name, lexicon) for name, lexicon in _entries(group)]
    result = "\n\n".join(blocks)
    assert result.startswith("#### `")
    assert len(blocks) == len(_entries(group))
    return result


def bundle_table() -> str:
    lines = ["| bundle | members |", "| --- | --- |"]
    for name, bundle in sorted(BUNDLES.items()):
        assert isinstance(bundle, Bundle)
        members = ", ".join(f"`{member.name}`" for member in bundle.members)
        lines.append(f"| `{name}` | {members} |")
    result = "\n".join(lines)
    assert result.startswith("| bundle |")
    assert len(lines) == len(BUNDLES) + 2
    return result


def readme_for_site() -> str:
    """Return README.md with its GitHub-relative `docs/...` links rewritten for zensical.

    README.md is written to render correctly as GitHub's repo-root file, so its own links to
    other doc pages are repo-root-relative (`docs/rules.md`). Once built as docs/index.md
    though, the page lives inside docs_dir, where those same links must be relative to that
    directory instead (`rules.md`), so the leading `docs/` segment is stripped.
    """
    text = README_PATH.read_text()
    result = re.sub(r'(?<=\]\()docs/|(?<=src=")docs/', "", text)
    assert "](docs/" not in result
    assert 'src="docs/' not in result
    return result


def define_env(env: Any) -> None:
    assert hasattr(env, "macro"), "zensical macros plugin must supply a MacroEnv"
    env.macro(lexicon_table)
    env.macro(bundle_table)
    env.macro(readme_for_site)
    assert "lexicon_table" in env.macros
    assert "bundle_table" in env.macros
    assert "readme_for_site" in env.macros
