from __future__ import annotations

import pytest

import lexguard
from lexguard.words import GROUPS, LEXICONS

pytestmark = pytest.mark.unit


def test_names_are_unique_across_groups():
    total = sum(len(group) for group in GROUPS.values())
    assert total == len(LEXICONS), "a name collision silently dropped a lexicon from the registry"


def test_groups_partition_the_registry():
    seen: set[str] = set()
    for group in GROUPS.values():
        assert seen.isdisjoint(group), "a lexicon appears in two groups"
        seen |= set(group)
    assert seen == set(LEXICONS), "every lexicon belongs to exactly one group"


@pytest.mark.parametrize("lexicon", LEXICONS.values(), ids=LEXICONS.keys())
def test_every_lexicon_is_well_formed(lexicon):
    assert lexicon.indicates, "a lexicon must indicate something"
    assert lexicon.fix, "a lexicon must carry a fix"
    assert lexicon.examples(), "a lexicon can produce examples"


@pytest.mark.parametrize("lexicon", LEXICONS.values(), ids=LEXICONS.keys())
def test_every_lexicon_is_exported_from_the_package(lexicon):
    assert getattr(lexguard, lexicon.label, None) is lexicon, (
        f"{lexicon.label} is not re-exported from lexguard"
    )


@pytest.mark.parametrize("lexicon", LEXICONS.values(), ids=LEXICONS.keys())
def test_evidence_urls_are_persistent_links(lexicon):
    for source in lexicon.evidence:
        assert not source.url or source.url.startswith("https://"), (
            f"{lexicon.name}: {source.cite} url must be an https link or empty"
        )
