from __future__ import annotations

import argparse
import re
import sys

from .words import GROUPS, LEXICONS


def _slug(name: str) -> str:
    # the shipped lexicons name themselves in snake_case; normalise whatever was typed to match
    result = re.sub(r"[^\w]+", "_", name.strip()).strip("_").casefold()
    assert " " not in result
    return result


def _symbol(name: str) -> str:
    # snake_case name -> PascalCase variable, the form the built-ins are exported and bound under
    result = "".join(part.capitalize() for part in re.split(r"[^a-z0-9]+", name) if part)
    assert "_" not in result
    return result


def ls(args: argparse.Namespace) -> int:
    for label, group in GROUPS.items():
        symbols = ", ".join(_symbol(name) for name in sorted(group))
        print(f"{label} ({len(group)}): {symbols}")
    return 0


# resolve either the snake_case name ("due_date") or the PascalCase symbol ("DueDate") ls prints
_ALIASES = {alias: name for name in LEXICONS for alias in (name, _slug(_symbol(name)))}


def show(args: argparse.Namespace) -> int:
    name = _ALIASES.get(_slug(args.name))
    if name is None:
        print(f"no built-in lexicon named {args.name!r}; try 'lexguard ls'", file=sys.stderr)
        return 2
    print(f"{_symbol(name)} = {LEXICONS[name].as_code()}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lexguard",
        description="Discover the built-in lexicons and pull them into your code as source.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_ls = sub.add_parser("ls", help="list the built-in lexicons by group")
    p_ls.set_defaults(func=ls)

    p_show = sub.add_parser(
        "show",
        help="print a built-in lexicon as paste-able code to own and edit",
        description="Print a built-in lexicon as a paste-able Lexicon binding. Append it to a "
        "module ('lexguard show slop >> mylexicons.py') and edit the terms as code.",
    )
    p_show.add_argument("name", help="the built-in lexicon's name or symbol, e.g. slop or Slop")
    p_show.set_defaults(func=show)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = args.func(args)
    assert isinstance(result, int)
    return result


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
