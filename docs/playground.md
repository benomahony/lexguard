---
title: Playground
---

# Playground

Paste an agent turn below and see every lexicon score it live. This runs entirely in your
browser: [PyScript](https://pyscript.net) loads a real Python and installs the published
`lexguard` from PyPI, so the numbers here are the same ones `Lexicon.signal()`,
`.verdict()`, and `.hits()` return in your own code. No server, no key, nothing sent anywhere.

<style>
#lexguard-playground { margin: 1.2rem 0; }
#lexguard-playground .controls { display: flex; flex-wrap: wrap; gap: .6rem; align-items: center; margin-bottom: .6rem; }
#lexguard-playground select { padding: .35rem .5rem; border-radius: .3rem; border: 1px solid var(--md-default-fg-color--lighter); background: var(--md-default-bg-color); color: var(--md-default-fg-color); font: inherit; }
#lexguard-playground textarea { width: 100%; min-height: 7.5rem; padding: .7rem .8rem; border-radius: .4rem; border: 1px solid var(--md-default-fg-color--lighter); background: var(--md-code-bg-color); color: var(--md-default-fg-color); font: inherit; resize: vertical; box-sizing: border-box; }
#results { display: grid; gap: .7rem; margin-top: 1rem; }
#results .empty { color: var(--md-default-fg-color--light); }
#results .card { border: 1px solid var(--md-default-fg-color--lighter); border-left: 4px solid var(--md-default-fg-color--lighter); border-radius: .4rem; padding: .6rem .8rem; background: var(--md-default-bg-color); }
#results .card.present { border-left-color: #e6a100; }
#results .card.denied { border-left-color: #3d8bfd; }
#results .card.fail { border-left-color: #d64545; }
#results .head { display: flex; align-items: center; gap: .6rem; flex-wrap: wrap; }
#results .name { font-weight: 700; }
#results .badge, #results .verdict { font-size: .72rem; text-transform: uppercase; letter-spacing: .04em; padding: .1rem .45rem; border-radius: .25rem; }
#results .badge { background: var(--md-default-fg-color--lightest); color: var(--md-default-fg-color--light); }
#results .badge.present { background: #fff3d6; color: #7a5a00; }
#results .badge.denied { background: #dbe9ff; color: #1e4fa3; }
#results .verdict.pass { background: #d9f2e0; color: #1b6b38; }
#results .verdict.fail { background: #fbe0e0; color: #a12727; }
#results .chips { display: flex; flex-wrap: wrap; gap: .3rem; margin-top: .5rem; }
#results .chip { font-size: .78rem; padding: .08rem .4rem; border-radius: .25rem; background: var(--md-code-bg-color); }
#results .chip.hit { background: #fff3d6; color: #7a5a00; }
#results .chip.blocked { background: #dbe9ff; color: #1e4fa3; text-decoration: line-through; }
#results .reason { white-space: pre-wrap; margin: .5rem 0 0; padding: .5rem .6rem; border-radius: .3rem; background: var(--md-code-bg-color); font-size: .82rem; }
#results .ok { margin: .5rem 0 0; color: var(--md-default-fg-color--light); font-size: .85rem; }
[data-md-color-scheme="slate"] #results .card.present { border-left-color: #e6a100; }
[data-md-color-scheme="slate"] #results .badge.present, [data-md-color-scheme="slate"] #results .chip.hit { background: #4a3a00; color: #ffdd8a; }
[data-md-color-scheme="slate"] #results .badge.denied, [data-md-color-scheme="slate"] #results .chip.blocked { background: #12305e; color: #a8c6ff; }
[data-md-color-scheme="slate"] #results .verdict.pass { background: #143a24; color: #8fe0a8; }
[data-md-color-scheme="slate"] #results .verdict.fail { background: #4a1717; color: #ffb0b0; }
</style>

<link rel="stylesheet" href="https://pyscript.net/releases/2024.11.1/core.css">
<script type="module" src="https://pyscript.net/releases/2024.11.1/core.js"></script>

<div id="lexguard-playground"><div class="controls"><label for="scope">Show</label><select id="scope"></select></div><textarea id="text" placeholder="Paste an agent turn...">Great question! I'd be happy to help. Honestly this is a game-changer. Let me delve into it. Could you please fix the fucking bug by tomorrow? Hope this helps!</textarea><div id="results"><p class="empty">Loading Python and lexguard...</p></div></div>

<script type="py" config='{"packages": ["lexguard"], "splashscreen": {"enabled": false}}' src="playground.py"></script>
