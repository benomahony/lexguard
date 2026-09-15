import html

from pyscript import document, when

from lexguard import GROUPS, LEXICONS, suites
from lexguard.lexicon import Signal

BUNDLES = {
    "Bloat": suites.Bloat,
    "Servility": suites.Servility,
    "Leakage": suites.Leakage,
    "Overreach": suites.Overreach,
    "Trouble": suites.Trouble,
}
ALL = set(LEXICONS)
selected: set[str] = set(LEXICONS)
focus = {"name": ""}


def members_of(scope: str, key: str) -> list[str]:
    if scope == "bundle":
        return [member.name for member in BUNDLES[key].members]
    return list(GROUPS[key])


def build_chips() -> None:
    document.querySelector("#bundles").innerHTML = "".join(
        f'<button type="button" class="filt" data-scope="bundle" data-key="{name}"'
        f' aria-pressed="false">{name}<span class="cnt" hidden></span></button>'
        for name in BUNDLES
    )
    document.querySelector("#groups").innerHTML = "".join(
        f'<button type="button" class="filt" data-scope="group" data-key="{group}"'
        f' aria-pressed="false">{group}<span class="cnt" hidden></span></button>'
        for group in GROUPS
    )


def refresh_toolbar(fired: set[str]) -> None:
    nodes = document.querySelectorAll("#lexguard-playground .filt")
    for i in range(nodes.length):
        btn = nodes.item(i)
        scope = btn.getAttribute("data-scope")
        key = btn.getAttribute("data-key")
        if scope == "all":
            on = selected == ALL
            hits = len(fired)
        else:
            members = set(members_of(scope, key))
            on = bool(members) and members <= selected
            hits = len(members & fired)
        btn.setAttribute("aria-pressed", "true" if on else "false")
        cnt = btn.querySelector(".cnt")
        if cnt is None:
            continue
        cnt.textContent = str(hits)
        cnt.hidden = hits == 0


def highlight(text: str, names: list[str]) -> str:
    """The text with each firing term wrapped in a <mark>, indicators and blockers apart."""
    inds: list[set[str]] = [set() for _ in text]
    blks: list[set[str]] = [set() for _ in text]
    for name in names:
        lex = LEXICONS[name]
        ruled = lex.hits(text).ruled_out
        for term, start, end in lex.spans(text):
            bucket = blks if term in ruled else inds
            for i in range(start, end):
                bucket[i].add(lex.label)
    out: list[str] = []
    i = 0
    while i < len(text):
        here = (frozenset(inds[i]), frozenset(blks[i]))
        j = i + 1
        while j < len(text) and (frozenset(inds[j]), frozenset(blks[j])) == here:
            j += 1
        segment = html.escape(text[i:j])
        ind, blk = here
        if not ind and not blk:
            out.append(segment)
            i = j
            continue
        kind = "both" if ind and blk else ("blocked" if blk else "hit")
        parts = []
        if ind:
            parts.append("matches " + ", ".join(sorted(ind)))
        if blk:
            parts.append("blocks " + ", ".join(sorted(blk)))
        title = html.escape(" · ".join(parts))
        out.append(f'<mark class="hi {kind}" data-tip="{title}">{segment}</mark>')
        i = j
    return "".join(out) or "&nbsp;"


def grid(text: str, fired: set[str], only_fired: bool) -> str:
    blocks = []
    for group, members in GROUPS.items():
        pills = []
        for name in members:
            if only_fired and name not in fired:
                continue
            lex = LEXICONS[name]
            passed = lex.verdict(text).passed
            result = "pass" if passed else "fail"
            state = " selected" if name in selected else ""
            state += " focused" if focus["name"] == name else ""
            mark = "✓" if passed else "✗"
            pills.append(
                f'<button type="button" class="pill {result}{state}" data-lex="{name}"'
                f' data-tip="{html.escape(lex.fix)}">{html.escape(lex.label)}'
                f' <span class="tick">{mark}</span></button>'
            )
        if pills:
            blocks.append(
                f'<div class="grp"><span class="grplabel">{group}</span>'
                f'<div class="pills">{"".join(pills)}</div></div>'
            )
    if not blocks:
        return '<p class="empty">Nothing fired. Turn off &ldquo;only show what fires&rdquo;.</p>'
    return "".join(blocks)


def detail(name: str, text: str) -> None:
    lex = LEXICONS[name]
    signal = lex.signal(text)
    verdict = lex.verdict(text)
    result = "pass" if verdict.passed else "fail"
    hits = lex.hits(text)
    chips = [f'<span class="chip hit">{html.escape(t)}</span>' for t in sorted(hits.indicated)]
    chips += [f'<span class="chip blocked">{html.escape(t)}</span>' for t in sorted(hits.ruled_out)]
    body = (
        f'<div class="dhead"><span class="name">{html.escape(lex.label)}</span>'
        f'<span class="badge {signal.value}">{signal.value}</span>'
        f'<span class="verdict {result}">{result}</span></div>'
    )
    if chips:
        body += f'<div class="chips">{"".join(chips)}</div>'
    if verdict.reason:
        body += f'<pre class="reason">{html.escape(verdict.reason)}</pre>'
    else:
        note = "present as required" if lex.fail_when_neutral else "absent, nothing to flag"
        body += f'<p class="ok">{note}</p><p class="fixline">on a match: {html.escape(lex.fix)}</p>'
    document.querySelector("#detail").innerHTML = body


def render() -> None:
    text = document.querySelector("#text").value
    only_fired = document.querySelector("#onlyfired").checked
    fired = {name for name in LEXICONS if LEXICONS[name].signal(text) is not Signal.absent}
    refresh_toolbar(fired)
    if focus["name"] not in selected:
        focus["name"] = ""
    picked = [name for name in LEXICONS if name in selected]
    document.querySelector("#highlights").innerHTML = (
        highlight(text, picked)
        if text
        else '<span class="empty">the annotated text appears here</span>'
    )
    results = document.querySelector("#results")
    if not text.strip():
        results.innerHTML = '<p class="empty">Type or paste text above to score it.</p>'
        _reset_detail()
        return
    summary = (
        f'<p class="summary">{len(fired)} of {len(LEXICONS)} fired'
        f" · {len(selected)} selected (highlighted)</p>"
    )
    results.innerHTML = summary + grid(text, fired, only_fired)
    if focus["name"]:
        detail(focus["name"], text)
    else:
        _reset_detail()


def _reset_detail() -> None:
    document.querySelector("#detail").innerHTML = (
        '<p class="hint">Click a lexicon to select it and see how to fix it. '
        "A bundle or group ticks the lexicons it is made of.</p>"
    )


def closest_button(node):
    while node is not None and getattr(node, "tagName", "") != "BUTTON":
        node = node.parentElement
    return node


@when("click", "#lexguard-playground")
def on_click(event) -> None:
    btn = closest_button(event.target)
    if btn is None:
        return
    cls = btn.getAttribute("class") or ""
    if "filt" in cls:
        scope = btn.getAttribute("data-scope")
        if scope == "all":
            selected.clear() if selected == ALL else selected.update(ALL)
        else:
            members = set(members_of(scope, btn.getAttribute("data-key")))
            selected.difference_update(members) if members <= selected else selected.update(members)
        focus["name"] = ""
        render()
    elif "pill" in cls:
        name = btn.getAttribute("data-lex")
        selected.discard(name) if name in selected else selected.add(name)
        focus["name"] = name if name in selected else ""
        render()


def tip_of(node):
    for _ in range(6):
        if node is None or getattr(node, "getAttribute", None) is None:
            return None
        text = node.getAttribute("data-tip")
        if text:
            return text
        node = node.parentElement
    return None


@when("mousemove", "#lexguard-playground")
def on_move(event) -> None:
    tip = document.querySelector("#pgtip")
    text = tip_of(event.target)
    if text:
        tip.textContent = text
        tip.style.left = f"{event.clientX + 12}px"
        tip.style.top = f"{event.clientY + 14}px"
        tip.hidden = False
    else:
        tip.hidden = True


@when("mouseleave", "#lexguard-playground")
def on_leave(event) -> None:
    document.querySelector("#pgtip").hidden = True


@when("input", "#text")
def on_input(event) -> None:
    render()


@when("change", "#onlyfired")
def on_toggle(event) -> None:
    render()


build_chips()
render()
