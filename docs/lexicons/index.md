# Lexicons

Every lexicon that ships with lexguard, rendered straight from `lexguard.words` and
`lexguard.suites` at build time by `docs/macros.py`, so a page can never drift from the code.
Import any of these by their class name, e.g. `from lexguard import DueDate`.

## Groups

- [Request](request.md): what the user is asking for — dates, priority, scope, ownership
- [Instruction](instruction.md): how the user asked for it to be shaped — format, length,
  tone, demands
- [Response](response.md): what a model's reply looks like — hedging, slop, sycophancy,
  refusals
- [Domain](domain.md): what the request is about — money, travel, household, people
- [Bundles](bundles.md): prebuilt groupings of the lexicons above
