from __future__ import annotations

import argparse
import os
import re
import shlex
import shutil
import subprocess
import sys

from .words import LEXICONS


def _slug(name: str) -> str:
    # normalise whatever was typed to the snake_case a lexicon names itself with
    result = re.sub(r"[^\w]+", "_", name.strip()).strip("_").casefold()
    assert " " not in result
    return result


def _symbol(name: str) -> str:
    # snake_case name -> PascalCase, the form the built-ins are exported and bound under
    result = "".join(part.capitalize() for part in re.split(r"[^a-z0-9]+", name) if part)
    assert "_" not in result
    return result


# resolve either the snake_case name ("due_date") or the PascalCase symbol ("DueDate") we list
_ALIASES = {alias: name for name in LEXICONS for alias in (name, _slug(_symbol(name)))}


def _picker() -> list[str] | None:
    # the interactive picker command, or None if there is none. $LEXGUARD_PICKER overrides;
    # otherwise use whichever fzf-compatible finder is on the PATH, with lexguard as its own
    # live preview. Any of these turns the bare command into a dropdown; none, and it lists.
    override = os.environ.get("LEXGUARD_PICKER")
    if override:
        return shlex.split(override)
    for finder in ("fzf", "sk"):  # sk == skim, a drop-in fzf clone with the same --preview
        found = shutil.which(finder)
        if found:
            return [found, "--preview", "lexguard {}"]
    return None


def _pick(symbols: list[str], command: list[str]) -> str | None:
    proc = subprocess.run(command, input="\n".join(symbols), capture_output=True, text=True)
    return proc.stdout.strip() or None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lexguard",
        description="List the built-in lexicons, or print one as source to paste into your code.",
    )
    parser.add_argument(
        "name",
        nargs="?",
        help="a lexicon name or symbol (e.g. slop or Slop); omit to list every lexicon",
    )
    query = parser.parse_args(argv).name

    if query is None:
        symbols = [_symbol(name) for name in sorted(LEXICONS)]
        # interactive with a picker available -> a dropdown; piped or picker-less -> the plain list
        picker = _picker()
        if sys.stdout.isatty() and picker:
            query = _pick(symbols, picker)
            if query is None:
                return 0
        else:
            print("\n".join(symbols))
            return 0

    name = _ALIASES.get(_slug(query))
    if name is None:
        print(f"no lexicon named {query!r}; run 'lexguard' to list them", file=sys.stderr)
        return 2
    print(f"{_symbol(name)} = {LEXICONS[name].as_code()}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
