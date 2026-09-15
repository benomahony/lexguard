---
title: Playground
---

# Playground

Paste an agent response and see every lexicon score it live in your browser.

<style>
#lexguard-playground { margin: 1.2rem 0; }
#lexguard-playground .scoperow { display: flex; gap: .5rem; align-items: baseline; margin-bottom: .5rem; flex-wrap: wrap; }
#lexguard-playground .scoperow .lbl { font-size: .68rem; text-transform: uppercase; letter-spacing: .06em; font-weight: 700; color: var(--md-default-fg-color--light); min-width: 4.2rem; }
#lexguard-playground .scopes { display: flex; flex-wrap: wrap; gap: .35rem; }
#lexguard-playground .filt, #lexguard-playground .pill { font: inherit; font-size: .8rem; line-height: 1.4; display: inline-flex; align-items: center; gap: .3rem; padding: .16rem .6rem; border-radius: 1rem; border: 1px solid var(--md-default-fg-color--lighter); background: var(--md-default-bg-color); color: var(--md-default-fg-color--light); cursor: pointer; }
#lexguard-playground .filt:hover, #lexguard-playground .pill:hover { border-color: var(--md-default-fg-color--light); color: var(--md-default-fg-color); }
#lexguard-playground .filt[aria-pressed="true"], #lexguard-playground .pill.selected { border-color: var(--md-primary-fg-color); background: color-mix(in srgb, var(--md-primary-fg-color) 12%, transparent); color: var(--md-primary-fg-color); font-weight: 600; }
#lexguard-playground .cnt { font-size: .72rem; font-weight: 700; color: #b8860b; }
[data-md-color-scheme="slate"] #lexguard-playground .cnt { color: #e6b84d; }
#lexguard-playground .rowend { display: flex; align-items: center; gap: .9rem; flex-wrap: wrap; margin: .2rem 0 .7rem; }
#lexguard-playground .onlyfired { display: inline-flex; align-items: center; gap: .4rem; font-size: .82rem; color: var(--md-default-fg-color--light); cursor: pointer; }
#lexguard-playground .editor textarea { box-sizing: border-box; width: 100%; min-height: 6rem; padding: .7rem .8rem; border-radius: .4rem; border: 1px solid var(--md-default-fg-color--lighter); background: var(--md-code-bg-color); color: var(--md-default-fg-color); font: inherit; font-size: .88rem; line-height: 1.6; resize: vertical; }
#lexguard-playground .editor textarea::placeholder { color: var(--md-default-fg-color--light); }
#lexguard-playground .annotated { margin-top: .5rem; padding: .7rem .8rem; border-radius: .4rem; background: var(--md-code-bg-color); border: 1px solid var(--md-default-fg-color--lightest); font: inherit; font-size: .88rem; line-height: 1.6; white-space: pre-wrap; overflow-wrap: break-word; }
#lexguard-playground .annotated .empty { color: var(--md-default-fg-color--light); }
#lexguard-playground #highlights mark.hi { color: inherit; background: transparent; border-radius: .15rem; padding: .05em 0; cursor: help; -webkit-box-decoration-break: clone; box-decoration-break: clone; }
#lexguard-playground #highlights mark.hi.hit { background: #fff3d6; box-shadow: inset 0 -.14em #e6a100; }
#lexguard-playground #highlights mark.hi.blocked { background: #dbe9ff; box-shadow: inset 0 -.14em #3d8bfd; }
#lexguard-playground #highlights mark.hi.both { background: #fff3d6; box-shadow: inset 0 -.14em #3d8bfd; }
#results { margin-top: 1rem; }
#results .summary { font-size: .82rem; color: var(--md-default-fg-color--light); margin: 0 0 .5rem; }
#results .empty { color: var(--md-default-fg-color--light); }
#results .grp { margin: .5rem 0; }
#results .grplabel { display: block; font-size: .66rem; text-transform: uppercase; letter-spacing: .06em; font-weight: 700; color: var(--md-default-fg-color--light); margin-bottom: .28rem; }
#results .pills { display: flex; flex-wrap: wrap; gap: .35rem; }
#lexguard-playground .pill .tick { font-weight: 700; line-height: 1; }
#lexguard-playground .pill.pass .tick { color: #1b8a4a; }
#lexguard-playground .pill.fail .tick { color: #c0392b; }
#lexguard-playground .pill.focused { outline: 2px solid var(--md-primary-fg-color); outline-offset: 1px; }
#pgtip { position: fixed; z-index: 100; max-width: 22rem; padding: .3rem .5rem; border-radius: .3rem; background: var(--md-default-fg-color); color: var(--md-default-bg-color); font-size: .76rem; line-height: 1.35; pointer-events: none; box-shadow: 0 2px 8px rgba(0,0,0,.25); }
#detail { margin-top: .9rem; padding-top: .6rem; border-top: 1px solid var(--md-default-fg-color--lightest); }
#detail .hint { color: var(--md-default-fg-color--light); font-size: .85rem; margin: .2rem 0; }
#detail .dhead { display: flex; align-items: center; gap: .5rem; margin-bottom: .2rem; }
#detail .dhead .name { font-weight: 700; }
#lexguard-playground .badge, #lexguard-playground .verdict { font-size: .72rem; text-transform: uppercase; letter-spacing: .04em; padding: .1rem .45rem; border-radius: .25rem; }
#lexguard-playground .badge { background: var(--md-default-fg-color--lightest); color: var(--md-default-fg-color--light); }
#lexguard-playground .badge.present { background: #fff3d6; color: #7a5a00; }
#lexguard-playground .badge.denied { background: #dbe9ff; color: #1e4fa3; }
#lexguard-playground .verdict.pass { background: #d9f2e0; color: #1b6b38; }
#lexguard-playground .verdict.fail { background: #fbe0e0; color: #a12727; }
#lexguard-playground .chips { display: flex; flex-wrap: wrap; gap: .3rem; margin: .4rem 0; }
#lexguard-playground .chip { font-size: .78rem; padding: .08rem .4rem; border-radius: .25rem; background: var(--md-code-bg-color); }
#lexguard-playground .chip.hit { background: #fff3d6; color: #7a5a00; }
#lexguard-playground .chip.blocked { background: #dbe9ff; color: #1e4fa3; text-decoration: line-through; }
#lexguard-playground .reason { white-space: pre-wrap; margin: .4rem 0 0; padding: .5rem .6rem; border-radius: .3rem; background: var(--md-code-bg-color); font-size: .82rem; }
#lexguard-playground .ok { margin: .4rem 0 0; color: var(--md-default-fg-color--light); font-size: .85rem; }
#lexguard-playground .fixline { margin: .3rem 0 0; font-size: .82rem; color: var(--md-default-fg-color--light); }
[data-md-color-scheme="slate"] #lexguard-playground #highlights mark.hi.hit { background: #4a3a00; }
[data-md-color-scheme="slate"] #lexguard-playground #highlights mark.hi.blocked { background: #12305e; }
[data-md-color-scheme="slate"] #lexguard-playground #highlights mark.hi.both { background: #4a3a00; }
[data-md-color-scheme="slate"] #lexguard-playground .pill.fail .tick { color: #ff9b93; }
[data-md-color-scheme="slate"] #lexguard-playground .pill.pass .tick { color: #8fe0a8; }
[data-md-color-scheme="slate"] #lexguard-playground .badge.present, [data-md-color-scheme="slate"] #lexguard-playground .chip.hit { background: #4a3a00; color: #ffdd8a; }
[data-md-color-scheme="slate"] #lexguard-playground .badge.denied, [data-md-color-scheme="slate"] #lexguard-playground .chip.blocked { background: #12305e; color: #a8c6ff; }
[data-md-color-scheme="slate"] #lexguard-playground .verdict.pass { background: #143a24; color: #8fe0a8; }
[data-md-color-scheme="slate"] #lexguard-playground .verdict.fail { background: #4a1717; color: #ffb0b0; }
</style>

<link rel="stylesheet" href="https://pyscript.net/releases/2024.11.1/core.css">
<script type="module" src="https://pyscript.net/releases/2024.11.1/core.js"></script>

<div id="lexguard-playground">
<div class="editor"><textarea id="text" placeholder="Paste an agent turn...">Great question! I'd be happy to help. Honestly this is a game-changer. Let me delve into it. Could you please fix the fucking bug by tomorrow? Hope this helps!</textarea><div id="highlights" class="annotated"></div></div>
<div class="rowend"><button type="button" class="filt everything" data-scope="all" data-key="" aria-pressed="true">Everything<span class="cnt" hidden></span></button><label class="onlyfired"><input type="checkbox" id="onlyfired"> only show what fires</label></div>
<div class="scoperow"><span class="lbl">Bundles</span><span class="scopes" id="bundles"></span></div>
<div class="scoperow"><span class="lbl">Groups</span><span class="scopes" id="groups"></span></div>
<div id="results"><p class="empty">Loading Python and lexguard...</p></div>
<div id="detail"></div>
<div id="pgtip" hidden></div>
</div>

<script type="py" config='{"packages": ["lexguard"], "splashscreen": {"enabled": false}}' src="playground.py"></script>
