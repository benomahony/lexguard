from __future__ import annotations

import argparse
import re
import sys

from .lexicon import Lexicon, parse
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


def draft(args: argparse.Namespace) -> int:
    terms = parse(sys.stdin.read())
    if not any(term.strip() for term in terms):
        print("no terms on stdin; pipe or type one term per line", file=sys.stderr)
        return 2
    name = _slug(args.name)
    lexicon = Lexicon(name=name, indicates=terms, rules_out=args.rules_out, fix=args.fix)
    lines = ["from lexguard import Lexicon", ""] if args.want_import else []
    lines.append(f"{_symbol(name)} = {lexicon.as_code()}")
    print("\n".join(lines))
    return 0


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
        description="Curate lexicons as reviewable code, straight from the terminal.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_draft = sub.add_parser(
        "draft",
        help="turn raw terms on stdin into a paste-able Lexicon definition",
        description="Read raw terms on stdin (one per line or comma-separated) and print a "
        "cleaned, sorted, ruff-formatted Lexicon binding ready to paste into a module.",
    )
    p_draft.add_argument("name", help="the lexicon's name (normalised to snake_case)")
    p_draft.add_argument("--fix", default="", help="the one-line fix advice for the lexicon")
    p_draft.add_argument(
        "--rules-out",
        default="",
        dest="rules_out",
        metavar="TERMS",
        help="terms that rule the concept out (comma-separated)",
    )
    p_draft.add_argument(
        "--import",
        action="store_true",
        dest="want_import",
        help="also emit the 'from lexguard import Lexicon' line",
    )
    p_draft.set_defaults(func=draft)

    p_ls = sub.add_parser("ls", help="list the built-in lexicons by group")
    p_ls.set_defaults(func=ls)

    p_show = sub.add_parser("show", help="print a built-in lexicon as paste-able code to fork")
    p_show.add_argument("name", help="the built-in lexicon's name, e.g. slop")
    p_show.set_defaults(func=show)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = args.func(args)
    assert isinstance(result, int)
    return result


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
