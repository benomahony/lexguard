from __future__ import annotations

import argparse
import shutil
import subprocess
import sys

from .words import LEXICONS


def _binding(name: str) -> str:
    # snake_case name -> the "Slop = ..." / "DueDate = ..." form the built-ins are bound under
    return "".join(part.capitalize() for part in name.split("_"))


def _pick(names: list[str], fzf: str) -> str | None:
    # hand the list to fzf with lexguard as its own live preview, and read back the choice
    chosen = subprocess.run(
        [fzf, "--preview", "lexguard {}"], input="\n".join(names), capture_output=True, text=True
    )
    return chosen.stdout.strip() or None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lexguard",
        description="List the built-in lexicons, or print one as source to paste into your code.",
    )
    parser.add_argument(
        "name",
        nargs="?",
        help="a lexicon name, e.g. slop; omit to list them all (or pick one, if fzf is installed)",
    )
    query = parser.parse_args(argv).name

    if query is None:
        names = sorted(LEXICONS)
        fzf = shutil.which("fzf")
        if fzf and sys.stdout.isatty():  # interactive with fzf around -> a picker with a preview
            query = _pick(names, fzf)
            if query is None:
                return 0
        else:  # piped, or no fzf -> a plain list you can compose (e.g. into fzf yourself)
            print("\n".join(names))
            return 0

    lexicon = LEXICONS.get(query.casefold())
    if lexicon is None:
        print(f"no lexicon named {query!r}; run 'lexguard' to list them", file=sys.stderr)
        return 2
    print(f"{_binding(lexicon.name)} = {lexicon.as_code()}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
