from __future__ import annotations

from lexguard.lexicon import Lexicon
from lexguard.words import (
    demand,
    epistemics,
    intent,
    manner,
    priority,
    progress,
    safety,
    shape,
    style,
    task,
    time,
    topic,
)

MODULES = {
    "time": time,
    "priority": priority,
    "task": task,
    "intent": intent,
    "shape": shape,
    "demand": demand,
    "style": style,
    "epistemics": epistemics,
    "manner": manner,
    "safety": safety,
    "progress": progress,
    "topic": topic,
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

__all__ = [
    "GROUPS",
    "LEXICONS",
    "demand",
    "epistemics",
    "intent",
    "manner",
    "priority",
    "progress",
    "safety",
    "shape",
    "style",
    "task",
    "time",
    "topic",
]
