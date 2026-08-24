from __future__ import annotations

import argparse
import sys

from .words import LEXICONS


def main(argv: list[str] | None = None) -> int:
    assert argv is None or isinstance(argv, list)
    parser = argparse.ArgumentParser(
        prog="lexguard",
        description="List the built-in lexicons, or print one as source to paste into your code.",
    )
    parser.add_argument(
        "name",
        nargs="?",
        help="a lexicon name, e.g. slop; omit to list every lexicon, one per line",
    )
    query = parser.parse_args(argv).name
    assert query is None or isinstance(query, str)

    if query is None:
        print("\n".join(sorted(LEXICONS)))
        return 0

    lexicon = LEXICONS.get(query.casefold())
    if lexicon is None:
        print(f"no lexicon named {query!r}; run 'lexguard' to list them", file=sys.stderr)
        return 2
    print(lexicon.as_code())
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
