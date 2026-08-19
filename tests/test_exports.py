from __future__ import annotations

import pytest

from lexica.lexicon import Lexicon
from lexica.words import domain, instruction, request, response

pytestmark = pytest.mark.unit

MODULES = [domain, instruction, request, response]


@pytest.mark.parametrize("module", MODULES, ids=lambda module: module.__name__)
def test_all_lexicons_are_exported(module) -> None:
    defined = {name for name, value in vars(module).items() if isinstance(value, Lexicon)}
    assert defined == set(module.__all__)
