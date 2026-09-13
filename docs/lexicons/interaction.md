---
render_macros: true
---

# Interaction

How a multi-turn interaction is going: rejection, frustration, unverified claims, scope creep,
being stuck. General signals, not tied to any one domain, applied to an agent transcript.

Each lexicon detects a raw semantic act, not a speaker. You wire it to whichever turn you care
about: run `rejection` over the user turn to catch the user rejecting the agent, or over the agent
turn to catch the agent pushing back; run `stuck` or `unverified_claim` over the agent turn. The
same language is the same lexicon whoever produced it.

{{ lexicon_table("interaction") }}
