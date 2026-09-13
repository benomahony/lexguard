from __future__ import annotations

from lexguard.lexicon import Lexicon
from lexguard.words import domain, instruction, request, response, session

MODULES = {
    "request": request,
    "instruction": instruction,
    "response": response,
    "domain": domain,
    "session": session,
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

__all__ = ["GROUPS", "LEXICONS", "domain", "instruction", "request", "response", "session"]
