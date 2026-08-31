from __future__ import annotations

import pytest

from lexguard import Check, Lexicon, ObserveSpec, Quantity, Slop

pytestmark = pytest.mark.unit


class Notes:
    def __init__(self, notes: str) -> None:
        self.notes = notes


def test_field_reads_from_a_mapping_output():
    verdicts = Check([Slop], field="notes").run({"notes": "let us delve in"}, "explain")
    assert verdicts[0].passed is False


def test_field_path_through_a_leaf_value_resolves_to_nothing():
    verdicts = Check([Slop], field="notes.length").run(Notes(notes="clean text"), "explain")
    assert verdicts is None


def test_check_returns_none_for_a_blank_output():
    assert Check([Slop]).run("   ", "explain") is None


def test_observe_spec_returns_none_for_a_blank_output():
    assert ObserveSpec([Slop]).signals("   ", "explain") is None


def test_hits_works_for_a_lexicon_with_no_multiword_indicators():
    assert Quantity._indicate is None
    assert Quantity.hits("bring a dozen eggs") == {"dozen"}


def test_a_casefold_expanding_hit_has_no_span_in_the_original_text():
    lexicon = Lexicon(name="t", indicates=["strasse report"], fix="x")
    text = "the straße report is ready"
    assert lexicon.hits(text) == {"strasse report"}
    assert lexicon.spans(text) == []
