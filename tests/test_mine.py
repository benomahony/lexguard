from __future__ import annotations

import json

import pytest

from lexguard.lexicon import Lexicon
from lexguard.mine import (
    Label,
    Miner,
    Trace,
    associate,
    evaluate,
    extract_traces,
    fdr,
    from_attribute,
    mine,
    normalize,
)
from lexguard.mine.traces import Message

pytestmark = pytest.mark.unit


# --- stats ---------------------------------------------------------------------------------------


def test_associate_recovers_a_crude_odds_ratio():
    # present: 8 fail / 2 ok, absent: 2 fail / 8 ok  ->  (8*8)/(2*2) = 16
    result = associate([(8, 2, 2, 8)])
    assert result.odds_ratio == pytest.approx(16.0)
    assert result.z > 0 and result.p < 0.05
    assert result.support == 10


def test_association_below_one_when_presence_tracks_success():
    result = associate([(2, 8, 8, 2)])
    assert result.odds_ratio < 1 and result.z < 0


def test_stratifying_pools_away_a_confound():
    # within each stratum the odds ratio is 1, but a naive pooled table looks like an effect
    strata = [(30, 30, 5, 5), (2, 20, 2, 20)]
    naive = associate([(32, 50, 7, 25)])
    adjusted = associate(strata)
    assert naive.odds_ratio > 2
    assert adjusted.odds_ratio == pytest.approx(1.0, abs=0.25)


def test_empty_margin_stratum_contributes_nothing():
    # a stratum where the phrase never appears must not change the estimate
    with_empty = associate([(8, 2, 2, 8), (0, 0, 5, 5)])
    without = associate([(8, 2, 2, 8)])
    assert with_empty.odds_ratio == pytest.approx(without.odds_ratio)


def test_no_discordant_mass_reports_no_signal():
    result = associate([(0, 0, 0, 0)])
    assert result.odds_ratio == 1.0 and result.p == 1.0


def test_fdr_is_bounded_and_monotone():
    q = fdr({"a": 0.001, "b": 0.02, "c": 0.5, "d": 0.9})
    assert all(0.0 <= v <= 1.0 for v in q.values())
    assert q["a"] <= q["b"] <= q["c"] <= q["d"]
    assert q["d"] == pytest.approx(0.9)


# --- trace extraction ----------------------------------------------------------------------------


def _events_span(tid, user, assistant):
    return {
        "traceId": tid,
        "attributes": [{"key": "eval.passed", "value": {"boolValue": True}}],
        "events": [
            {
                "name": "gen_ai.user.message",
                "attributes": [{"key": "content", "value": {"stringValue": user}}],
            },
            {
                "name": "gen_ai.choice",
                "attributes": [{"key": "content", "value": {"stringValue": assistant}}],
            },
        ],
    }


def test_extract_maps_roles_to_groups_from_events():
    traces = extract_traces(
        {"resourceSpans": [{"scopeSpans": [{"spans": [_events_span("t", "hi", "there")]}]}]}
    )
    assert len(traces) == 1
    groups = {m.group: m.content for m in traces[0].messages}
    assert groups == {"request": "hi", "response": "there"}
    assert traces[0].attributes["eval.passed"] is True


def test_extract_reads_indexed_prompt_completion_attributes():
    span = {
        "traceId": "t",
        "attributes": [
            {"key": "gen_ai.prompt.0.role", "value": {"stringValue": "system"}},
            {"key": "gen_ai.prompt.0.content", "value": {"stringValue": "be terse"}},
            {"key": "gen_ai.prompt.1.role", "value": {"stringValue": "user"}},
            {"key": "gen_ai.prompt.1.content", "value": {"stringValue": "explain caching"}},
            {"key": "gen_ai.completion.0.role", "value": {"stringValue": "assistant"}},
            {"key": "gen_ai.completion.0.content", "value": {"stringValue": "it stores results"}},
        ],
    }
    (trace,) = extract_traces([span])
    by_group = {m.group: m.content for m in trace.messages}
    assert by_group == {
        "instruction": "be terse",
        "request": "explain caching",
        "response": "it stores results",
    }


def test_extract_reads_input_output_messages_json():
    span = {
        "traceId": "t",
        "attributes": [
            {
                "key": "gen_ai.input.messages",
                "value": {"stringValue": json.dumps([{"role": "user", "content": "hi"}])},
            },
            {
                "key": "gen_ai.output.messages",
                "value": {
                    "stringValue": json.dumps(
                        [{"role": "assistant", "parts": [{"type": "text", "content": "hello"}]}]
                    )
                },
            },
        ],
    }
    (trace,) = extract_traces([span])
    assert {(m.group, m.content) for m in trace.messages} == {
        ("request", "hi"),
        ("response", "hello"),
    }


def test_spans_sharing_a_trace_id_merge():
    payload = [_events_span("t", "a", "b"), _events_span("t", "c", "d")]
    (trace,) = extract_traces(payload)
    assert trace.text("request") == "a\nc"
    assert trace.text("response") == "b\nd"


# --- labels --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, Label.success),
        (False, Label.failure),
        ("pass", Label.success),
        ("FAIL", Label.failure),
        (1, Label.success),
        (0, Label.failure),
        (None, Label.abstain),
        ("mumble", Label.abstain),
    ],
)
def test_normalize_coerces_judge_output(value, expected):
    assert normalize(value) is expected


def test_from_attribute_reads_a_stored_verdict():
    label = from_attribute("eval.passed")
    passed = Trace("t", (), {"eval.passed": True})
    failed = Trace("t", (), {"eval.passed": False})
    missing = Trace("t", (), {})
    assert label(passed) is Label.success
    assert label(failed) is Label.failure
    assert label(missing) is Label.abstain


def test_a_plain_callable_is_a_labeller():
    # a live judge is just a function; mine() only needs Trace -> outcome
    def judge(trace: Trace) -> bool:
        return "sorry" not in trace.text("response")

    yes = Trace("t", (Message("assistant", "here it is", "response"),))
    no = Trace("t", (Message("assistant", "sorry, no", "response"),))
    assert normalize(judge(yes)) is Label.success
    assert normalize(judge(no)) is Label.failure


# --- mining --------------------------------------------------------------------------------------


def _trace(tid, response, *, passed, **attrs):
    return Trace(
        tid, (Message("assistant", response, "response"),), {"eval.passed": passed, **attrs}
    )


def test_mine_separates_failure_and_success_wording():
    traces = []
    for i in range(30):
        traces.append(_trace(f"f{i}", "sorry, i'm not sure this is right", passed=False))
        traces.append(_trace(f"s{i}", "run migrate then restart the worker", passed=True))
    sugg = mine(traces, label=from_attribute("eval.passed"), min_support=5)
    indicates = {c.phrase for c in sugg.indicates}
    rules_out = {c.phrase for c in sugg.rules_out}
    assert "sorry" in indicates
    assert "the" not in indicates and "the" not in rules_out  # stopword dropped
    assert rules_out & {"migrate", "restart", "worker"}
    assert all(c.leaning is Label.failure for c in sugg.indicates)


def test_confounder_adjustment_drops_a_spurious_phrase():
    traces = []
    # "sorry" genuinely marks failure in both task strata; "widget" only marks the hard task,
    # which fails more often, so it is spurious. Overlap within hard lets stratification see that.
    for i in range(36):
        traces.append(_trace(f"e{i}", "apply the patch and rerun", passed=True, task="easy"))
    for i in range(4):
        traces.append(
            _trace(f"ef{i}", "apply the patch and rerun sorry", passed=False, task="easy")
        )
    for i in range(6):
        traces.append(_trace(f"hs{i}", "configure the widget and deploy", passed=True, task="hard"))
    for i in range(6):
        traces.append(_trace(f"hsn{i}", "configure and deploy", passed=True, task="hard"))
    for i in range(14):
        traces.append(
            _trace(f"hf{i}", "configure the widget and deploy sorry", passed=False, task="hard")
        )
    for i in range(14):
        traces.append(_trace(f"hfn{i}", "configure and deploy sorry", passed=False, task="hard"))

    crude = mine(traces, label=from_attribute("eval.passed"), min_support=5)
    adjusted = mine(
        traces, label=from_attribute("eval.passed"), confounders=("task",), min_support=5
    )
    crude_phrases = {c.phrase for c in crude.indicates}
    adjusted_phrases = {c.phrase for c in adjusted.indicates}
    assert "widget" in crude_phrases  # naive mining is fooled
    assert "widget" not in adjusted_phrases  # stratifying on task removes it
    assert "sorry" in adjusted_phrases  # the genuine signal survives


def test_abstain_traces_are_dropped():
    traces = [
        _trace("a", "sorry not sure", passed=False),
        _trace("b", "run migrate", passed=True),
        Trace("c", (Message("assistant", "no verdict here", "response"),), {}),  # no eval.passed
    ]
    sugg = mine(traces, label=from_attribute("eval.passed"), min_support=1)
    assert sugg.n == 2


def test_suggest_builds_a_curatable_lexicon():
    traces = []
    for i in range(20):
        traces.append(_trace(f"f{i}", "sorry i cannot help", passed=False))
        traces.append(_trace(f"s{i}", "deploy the release now", passed=True))
    lex = mine(traces, label=from_attribute("eval.passed"), min_support=3).suggest(
        "apologetic", fix="commit to an answer"
    )
    assert isinstance(lex, Lexicon)
    assert lex.name == "apologetic" and lex.fix == "commit to an answer"
    assert lex.fires("sorry, i really cannot help with that")


def test_evaluate_scores_a_lexicon_on_held_out_traces():
    lex = Lexicon(name="apology", indicates=["sorry", "apologies"])
    held_out = [
        _trace("a", "sorry about that", passed=False),
        _trace("b", "apologies, my mistake", passed=False),
        _trace("c", "the answer is 42", passed=True),
        _trace("d", "deploy at noon", passed=True),
    ]
    card = evaluate(lex, held_out, label=from_attribute("eval.passed"))
    assert card.precision == 1.0 and card.recall == 1.0 and card.f1 == 1.0
    assert card.n == 4 and card.support == 2


# --- online mining -------------------------------------------------------------------------------


def _stream():
    for i in range(30):
        yield _trace(f"f{i}", "sorry, i'm not sure this is right", passed=False)
        yield _trace(f"s{i}", "run migrate then restart the worker", passed=True)


def test_online_observe_matches_offline_mine():
    traces = list(_stream())
    offline = mine(traces, label=from_attribute("eval.passed"))
    miner = Miner()
    for trace in traces:
        miner.observe(trace, trace.attributes["eval.passed"])  # label as you go, with anything
    online = miner.suggest()
    assert [c.phrase for c in online.indicates] == [c.phrase for c in offline.indicates]
    assert [c.phrase for c in online.rules_out] == [c.phrase for c in offline.rules_out]
    assert online.n == offline.n == 60


def test_observe_accepts_any_verdict_shape():
    miner = Miner()
    miner.observe(_trace("a", "sorry not sure", passed=False), "fail")
    miner.observe(_trace("b", "deploy now", passed=True), True)
    miner.observe(_trace("c", "restart worker", passed=True), 1)
    assert miner.n == 3 and miner.failures == 1


def test_observe_can_abstain_with_none():
    miner = Miner()
    miner.observe(_trace("a", "sorry", passed=False), None)
    assert miner.n == 0


def test_miner_polls_as_evidence_accumulates():
    miner = Miner()
    # too little to clear the false-discovery cut yet
    for i in range(2):
        miner.observe(_trace(f"f{i}", "sorry not sure", passed=False), Label.failure)
        miner.observe(_trace(f"s{i}", "deploy the worker", passed=True), Label.success)
    assert miner.suggest().indicates == ()
    # keep streaming and the signal emerges from the same miner
    for i in range(2, 30):
        miner.observe(_trace(f"f{i}", "sorry not sure", passed=False), Label.failure)
        miner.observe(_trace(f"s{i}", "deploy the worker", passed=True), Label.success)
    assert "sorry" in {c.phrase for c in miner.suggest().indicates}


def test_miner_default_label_and_extend():
    miner = Miner(label=from_attribute("eval.passed"))
    miner.extend(list(_stream()))  # labeller comes from the miner
    assert "sorry" in {c.phrase for c in miner.suggest().indicates}
    # a bare observe() with no outcome also uses the stored labeller
    miner.observe(_trace("x", "sorry again", passed=False))
    assert miner.n == 61


def test_miner_observe_without_label_is_an_error():
    with pytest.raises(AssertionError):
        Miner().observe(_trace("a", "sorry", passed=False))


def test_miner_state_pickles_for_checkpointing():
    import pickle

    miner = Miner(confounders=("length",))
    for trace in _stream():
        miner.observe(trace, trace.attributes["eval.passed"])
    restored = pickle.loads(pickle.dumps(miner))
    assert restored.n == miner.n
    assert [c.phrase for c in restored.suggest().indicates] == [
        c.phrase for c in miner.suggest().indicates
    ]
