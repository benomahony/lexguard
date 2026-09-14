# Lexicons

Every lexicon that ships with lexguard, rendered straight from `lexguard.words` and
`lexguard.suites` at build time by `docs/macros.py`, so a page can never drift from the code.
Import any of these by their class name, e.g. `from lexguard import DueDate`.

## Groups

Every lexicon detects a raw semantic act and is speaker agnostic, so these groups are facets of
meaning, not a split by who is speaking. Run any of them over whichever turn you care about.

- [Time](time.md): when something should happen (dates, deadlines, recurrence, duration)
- [Priority](priority.md): how urgent and how much effort (priority, effort, energy)
- [Task](task.md): the task itself (actions, lifecycle, structure, ownership)
- [Intent](intent.md): what an utterance is doing (questions, confirmation, correction, reference)
- [Shape](shape.md): how the output should be shaped (format, length, tone)
- [Demand](demand.md): what the output must include or do (citations, opinion, comparison, roleplay)
- [Style](style.md): writing tics to avoid (slop, filler, preamble, engagement bait)
- [Epistemics](epistemics.md): how claims are grounded (hedging, overclaiming, sourcing, uncertainty)
- [Tone](tone.md): how it comes across (politeness, rudeness, sycophancy, persona, affect)
- [Safety](safety.md): security and disclosure (refusal, prompt injection, secrets, config leaks)
- [Progress](progress.md): how the interaction is going (rejection, being stuck, scope creep)
- [Topic](topic.md): what the message is about (money, travel, household, people)
- [Bundles](bundles.md): prebuilt groupings of the lexicons above
