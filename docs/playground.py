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

selected_bundles: set[str] = set()
selected_groups: set[str] = set()
state = {"all": True}


def build_chips() -> None:
    document.querySelector("#bundles").innerHTML = "".join(
        f'<button type="button" class="tog" data-scope="bundle" data-key="{name}"'
        f' aria-pressed="false">{name}</button>'
        for name in BUNDLES
    )
    document.querySelector("#groups").innerHTML = "".join(
        f'<button type="button" class="tog" data-scope="group" data-key="{group}"'
        f' aria-pressed="false">{group}</button>'
        for group in GROUPS
    )


def sync_pressed() -> None:
    nodes = document.querySelectorAll("#lexguard-playground .tog")
    for i in range(nodes.length):
        btn = nodes.item(i)
        scope = btn.getAttribute("data-scope")
        key = btn.getAttribute("data-key")
        if scope == "all":
            on = state["all"]
        elif scope == "bundle":
            on = key in selected_bundles
        else:
            on = key in selected_groups
        btn.setAttribute("aria-pressed", "true" if on else "false")


def selected_names() -> list[str]:
    if state["all"]:
        return list(LEXICONS)
    chosen: set[str] = set()
    for bundle in selected_bundles:
        chosen.update(member.name for member in BUNDLES[bundle].members)
    for group in selected_groups:
        chosen.update(GROUPS[group])
    return [name for name in LEXICONS if name in chosen]


def chips(terms: frozenset[str], kind: str) -> str:
    if not terms:
        return ""
    tags = "".join(f'<span class="chip {kind}">{html.escape(t)}</span>' for t in sorted(terms))
    return f'<div class="chips">{tags}</div>'


def card(lex: Lexicon, text: str) -> str:
    signal = lex.signal(text)
    verdict = lex.verdict(text)
    hits = lex.hits(text)
    result = "pass" if verdict.passed else "fail"
    detail = chips(hits.indicated, "hit") + chips(hits.ruled_out, "blocked")
    if verdict.reason:
        detail += f'<pre class="reason">{html.escape(verdict.reason)}</pre>'
    else:
        note = "present as required" if lex.fail_when_neutral else "clean, no match"
        detail += f'<p class="ok">{note}</p>'
    return (
        f'<div class="card {signal.value} {result}">'
        f'<div class="head"><span class="name">{html.escape(lex.label)}</span>'
        f'<span class="badge {signal.value}">{signal.value}</span>'
        f'<span class="verdict {result}">{"pass" if verdict.passed else "fail"}</span></div>'
        f"{detail}</div>"
    )


def render() -> None:
    text = document.querySelector("#text").value
    only_fired = document.querySelector("#onlyfired").checked
    results = document.querySelector("#results")
    if not text.strip():
        results.innerHTML = '<p class="empty">Type or paste text above to score it.</p>'
        return
    names = selected_names()
    if not names:
        results.innerHTML = '<p class="empty">Pick a bundle or group, or choose Everything.</p>'
        return
    fired = sum(1 for name in names if LEXICONS[name].signal(text) is not Signal.absent)
    summary = f'<p class="summary">{fired} fired of {len(names)} selected</p>'
    cards = [
        card(LEXICONS[name], text)
        for name in names
        if not (only_fired and LEXICONS[name].signal(text) is Signal.absent)
    ]
    body = "".join(cards) if cards else '<p class="empty">Nothing fired in the selected set.</p>'
    results.innerHTML = summary + body


@when("click", "#lexguard-playground")
def on_click(event) -> None:
    btn = event.target
    if "tog" not in (btn.getAttribute("class") or ""):
        return
    scope = btn.getAttribute("data-scope")
    if scope == "all":
        state["all"] = True
        selected_bundles.clear()
        selected_groups.clear()
    else:
        target = selected_bundles if scope == "bundle" else selected_groups
        key = btn.getAttribute("data-key")
        target.discard(key) if key in target else target.add(key)
        state["all"] = False
    sync_pressed()
    render()


@when("input", "#text")
def on_input(event) -> None:
    render()


@when("change", "#onlyfired")
def on_toggle(event) -> None:
    render()


build_chips()
sync_pressed()
render()
