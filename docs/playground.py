import html

from pyscript import document, when

from lexguard import GROUPS, LEXICONS, suites
from lexguard.lexicon import Lexicon, Signal

BUNDLES = {
    "Bloat": suites.Bloat,
    "Servility": suites.Servility,
    "Leakage": suites.Leakage,
    "Overreach": suites.Overreach,
    "Trouble": suites.Trouble,
}


def build_scopes() -> None:
    parts = ['<option value="all">All lexicons: show what fires</option>']
    parts.append('<optgroup label="Bundles">')
    parts += [f'<option value="bundle:{name}">{name}</option>' for name in BUNDLES]
    parts.append("</optgroup>")
    parts.append('<optgroup label="Groups">')
    parts += [f'<option value="group:{group}">{group}</option>' for group in GROUPS]
    parts.append("</optgroup>")
    parts.append('<optgroup label="Every lexicon">')
    for label, name in sorted((lex.label, lex.name) for lex in LEXICONS.values()):
        parts.append(f'<option value="lex:{name}">{label}</option>')
    parts.append("</optgroup>")
    document.querySelector("#scope").innerHTML = "".join(parts)


def selection() -> tuple[list[Lexicon], bool]:
    value = document.querySelector("#scope").value
    if value == "all":
        return list(LEXICONS.values()), True
    kind, _, key = value.partition(":")
    if kind == "bundle":
        return list(BUNDLES[key].members), False
    if kind == "group":
        return list(GROUPS[key].values()), False
    return [LEXICONS[key]], False


def chips(terms: frozenset[str], kind: str) -> str:
    if not terms:
        return ""
    tags = "".join(f'<span class="chip {kind}">{html.escape(t)}</span>' for t in sorted(terms))
    return f'<div class="chips">{tags}</div>'


def card(lex: Lexicon, text: str) -> str:
    signal = lex.signal(text)
    verdict = lex.verdict(text)
    hits = lex.hits(text)
    state = "pass" if verdict.passed else "fail"
    detail = chips(hits.indicated, "hit") + chips(hits.ruled_out, "blocked")
    if verdict.reason:
        detail += f'<pre class="reason">{html.escape(verdict.reason)}</pre>'
    else:
        note = "present as required" if lex.fail_when_neutral else "clean, no match"
        detail += f'<p class="ok">{note}</p>'
    return (
        f'<div class="card {signal.value} {state}">'
        f'<div class="head"><span class="name">{html.escape(lex.label)}</span>'
        f'<span class="badge {signal.value}">{signal.value}</span>'
        f'<span class="verdict {state}">{"pass" if verdict.passed else "fail"}</span></div>'
        f"{detail}</div>"
    )


def render(event=None) -> None:
    text = document.querySelector("#text").value
    lexicons, only_fired = selection()
    results = document.querySelector("#results")
    if not text.strip():
        results.innerHTML = '<p class="empty">Type or paste text above to score it.</p>'
        return
    cards = [
        card(lex, text)
        for lex in lexicons
        if not (only_fired and lex.signal(text) is Signal.absent)
    ]
    results.innerHTML = (
        "".join(cards) if cards else '<p class="empty">Nothing fired for this text.</p>'
    )


build_scopes()
when("input", "#text")(render)
when("change", "#scope")(render)
render()
