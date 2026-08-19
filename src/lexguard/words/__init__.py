from __future__ import annotations

from ..lexicon import Lexicon
from . import domain, instruction, request, response

MODULES = {
    "request": request,
    "instruction": instruction,
    "response": response,
    "domain": domain,
}

LEXICONS: dict[str, Lexicon] = {
    entry.name: entry
    for module in MODULES.values()
    for entry in vars(module).values()
    if isinstance(entry, Lexicon)
}

GROUPS: dict[str, dict[str, Lexicon]] = {
    label: {entry.name: entry for entry in vars(module).values() if isinstance(entry, Lexicon)}
    for label, module in MODULES.items()
}

__all__ = ["GROUPS", "LEXICONS", "domain", "instruction", "request", "response"]
