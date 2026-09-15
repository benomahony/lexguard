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
NAME_GROUP = {name: group for group, members in GROUPS.items() for name in members}

selected_bundles: set[str] = set()
selected_groups: set[str] = set()
state = {"all": True, "focus": ""}


def build_chips() -> None:
    document.querySelector("#bundles").innerHTML = "".join(
        f'<button type="button" class="tog" data-scope="bundle" data-key="{name}"'
        f' aria-pressed="false">{name}<span class="cnt" hidden></span></button>'
        for name in BUNDLES
    )
    document.querySelector("#groups").innerHTML = "".join(
        f'<button type="button" class="tog" data-scope="group" data-key="{group}"'
        f' aria-pressed="false">{group}<span class="cnt" hidden></span></button>'
        for group in GROUPS
    )


def members_of(scope: str, key: str) -> list[str]:
    if scope == "bundle":
        return [member.name for member in BUNDLES[key].members]
    return list(GROUPS[key])


def refresh_chips(fired: set[str]) -> None:
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
        cnt = btn.querySelector(".cnt")
        if scope == "all":
            hits = len(fired)
        else:
            hits = sum(1 for name in members_of(scope, key) if name in fired)
        cnt.textContent = str(hits)
        cnt.hidden = hits == 0


def selected_names() -> list[str]:
    if state["all"]:
        return list(LEXICONS)
    chosen: set[str] = set()
    for bundle in selected_bundles:
        chosen.update(members_of("bundle", bundle))
    for group in selected_groups:
        chosen.update(GROUPS[group])
    return [name for name in LEXICONS if name in chosen]


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
        out.append(f'<mark class="hi {kind}" title="{title}">{segment}</mark>')
        i = j
    return "".join(out) or "&nbsp;"


def wall(text: str, names: list[str], only_fired: bool, fired: set[str]) -> str:
    scope = set(names)
    blocks = []
    for group, members in GROUPS.items():
        pills = []
        for name in members:
            if name not in scope or (only_fired and name not in fired):
                continue
            lex = LEXICONS[name]
            passed = lex.verdict(text).passed
            result = "pass" if passed else "fail"
            active = " active" if state["focus"] == name else ""
            mark = "✓" if passed else "✗"
            pills.append(
                f'<button type="button" class="pill {result}{active}" data-lex="{name}"'
                f' title="{html.escape(lex.fix)}">{html.escape(lex.label)}'
                f' <span class="tick">{mark}</span></button>'
            )
        if pills:
            blocks.append(
                f'<div class="grp"><span class="grplabel">{group}</span>'
                f'<div class="pills">{"".join(pills)}</div></div>'
            )
    if not blocks:
        return '<p class="empty">Nothing fired in the selected set.</p>'
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
    names = selected_names()
    fired = {name for name in names if LEXICONS[name].signal(text) is not Signal.absent}
    refresh_chips(fired)
    if state["focus"] not in fired:
        state["focus"] = ""
    focused = [state["focus"]] if state["focus"] else names
    document.querySelector("#highlights").innerHTML = highlight(text, focused) if text else "&nbsp;"
    document.querySelector("#highlights").style.transform = f"translateY({-scroll_top()}px)"
    results = document.querySelector("#results")
    if not text.strip():
        results.innerHTML = '<p class="empty">Type or paste text above to score it.</p>'
        _reset_detail()
        return
    if not names:
        results.innerHTML = '<p class="empty">Pick a bundle or group, or choose Everything.</p>'
        _reset_detail()
        return
    summary = f'<p class="summary">{len(fired)} fired of {len(names)} selected</p>'
    results.innerHTML = summary + wall(text, names, only_fired, fired)
    if state["focus"]:
        detail(state["focus"], text)
    else:
        _reset_detail()


def _reset_detail() -> None:
    document.querySelector(
        "#detail"
    ).innerHTML = (
        '<p class="hint">Click a lexicon to highlight only its matches and see how to fix it.</p>'
    )


def scroll_top() -> int:
    return document.querySelector("#text").scrollTop


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
    if "tog" in cls:
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
        state["focus"] = ""
        render()
    elif "pill" in cls:
        name = btn.getAttribute("data-lex")
        state["focus"] = "" if state["focus"] == name else name
        render()


@when("input", "#text")
def on_input(event) -> None:
    render()


@when("scroll", "#text")
def on_scroll(event) -> None:
    offset = -event.target.scrollTop
    document.querySelector("#highlights").style.transform = f"translateY({offset}px)"


@when("change", "#onlyfired")
def on_toggle(event) -> None:
    render()


build_chips()
render()
