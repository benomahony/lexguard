from __future__ import annotations

import re

import pytest
from hypothesis import given
from hypothesis import strategies as st

from lexguard import Lexicon, Politeness, Quantity, Recurrence, Signal, Slop
from lexguard.lexicon import phrases, snippet, tidy

pytestmark = pytest.mark.unit


@given(st.lists(st.text()))
def test_tidy_entries_are_casefolded_and_nonblank(words):
    result = tidy(words)
    assert all(word == word.casefold() for word in result)
    assert all(word.strip() for word in result)


@given(st.lists(st.text()))
def test_tidy_is_idempotent(words):
    once = tidy(words)
    assert tidy(once) == once


@given(st.lists(st.text(min_size=1)))
def test_phrases_returns_none_iff_no_multiword_entry(words):
    tidied = tidy(words)
    pattern = phrases(tidied)
    assert (pattern is None) == (not any(" " in word for word in tidied))
    if pattern is not None:
        re.compile(pattern)


@given(st.data())
def test_snippet_respects_ellipsis_rules(data):
    text = data.draw(st.text(max_size=200))
    start = data.draw(st.integers(min_value=0, max_value=len(text)))
    end = data.draw(st.integers(min_value=start, max_value=len(text)))
    result = snippet(text, start, end)
    assert (result.startswith("…")) == (start > 34)
    assert (result.endswith("…")) == (len(text) - end > 34)


@given(st.text(max_size=500))
def test_spans_are_in_bounds_and_sorted(text):
    spans = Slop.spans(text)
    assert spans == sorted(spans, key=lambda span: span[1])
    assert all(0 <= start <= end <= len(text) for _, start, end in spans)


@given(st.text(max_size=500))
def test_matches_and_denied_are_mutually_exclusive(text):
    assert not (Recurrence.matches(text) and Recurrence.denied(text))


@given(st.text(max_size=500))
def test_signal_is_always_a_valid_member(text):
    assert Recurrence.signal(text) in Signal


def test_hits_works_for_a_lexicon_with_no_multiword_indicators():
    assert Quantity._indicate is None
    hits = Quantity.hits("bring a dozen eggs")
    assert hits.indicated == {"dozen"}
    assert hits.ruled_out == set()


def test_a_casefold_expanding_hit_has_no_span_in_the_original_text():
    lexicon = Lexicon(name="t", indicates=["strasse report"], fix="x")
    text = "the straße report is ready"
    assert lexicon.hits(text).indicated == {"strasse report"}
    assert lexicon.spans(text) == []


def test_hits_splits_indicated_from_ruled_out():
    hits = Politeness.hits("could you please fix the fucking bug")
    assert hits.indicated == {"could you", "please"}
    assert hits.ruled_out == {"fucking"}
    assert hits.terms == {"could you", "please", "fucking"}


def test_density_counts_repeats_that_hits_would_dedupe():
    once = Slop.density("delve into caching once")
    repeated = Slop.density("delve delve delve into caching")
    assert repeated.indicated > once.indicated
    assert (
        Slop.hits("delve into caching once").indicated
        == Slop.hits("delve delve delve into caching").indicated
    )


def test_density_is_zero_for_empty_text():
    density = Slop.density("")
    assert density.indicated == 0.0
    assert density.ruled_out == 0.0


def test_density_is_a_fraction_of_words():
    text = "delve " + "word " * 99
    density = Slop.density(text)
    assert density.indicated == pytest.approx(0.01)


def test_density_reaches_one_only_when_every_word_is_a_hit():
    density = Slop.density("delve delve delve")
    assert density.indicated == 1.0


def test_density_caps_at_one_when_a_phrase_overlaps_its_own_word():
    lexicon = Lexicon(name="t", indicates=["please", "please please"], fix="x")
    density = lexicon.density("please please")
    assert density.indicated == 1.0
