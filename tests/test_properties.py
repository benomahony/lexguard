from __future__ import annotations

import re

import pytest
from hypothesis import given
from hypothesis import strategies as st

from lexguard import Recurrence, Signal, Slop
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
def test_fires_and_denied_are_mutually_exclusive(text):
    assert not (Recurrence.fires(text) and Recurrence.denied(text))


@given(st.text(max_size=500))
def test_signal_is_always_a_valid_member(text):
    assert Recurrence.signal(text) in Signal
