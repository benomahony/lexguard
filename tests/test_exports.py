from __future__ import annotations

import pytest

from lexguard import LEXICONS
from lexguard.lexicon import Lexicon
from lexguard.words import domain, instruction, request, response

pytestmark = pytest.mark.unit

MODULES = [domain, instruction, request, response]


@pytest.mark.parametrize("module", MODULES, ids=lambda module: module.__name__)
def test_all_lexicons_are_exported(module) -> None:
    defined = {name for name, value in vars(module).items() if isinstance(value, Lexicon)}
    assert defined == set(module.__all__)


@pytest.mark.parametrize("lexicon", LEXICONS.values(), ids=LEXICONS.keys())
def test_every_shipped_lexicon_carries_a_fix(lexicon: Lexicon) -> None:
    # fix is a required field: every shipped lexicon must offer a non-empty remedy so a verdict
    # is actionable standing alone, not just a label.
    assert lexicon.fix, f"{lexicon.name} is missing a fix"
