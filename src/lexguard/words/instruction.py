from __future__ import annotations

from ..lexicon import Lexicon

FormatList = Lexicon(
    name="format_list",
    indicates=[
        "as a list",
        "bullet",
        "bullet points",
        "bullets",
        "checklist",
        "dot points",
        "itemise",
        "itemize",
        "list",
        "listed",
        "numbered",
    ],
    rules_out=[
        "essay",
        "full sentences",
        "no bullets",
        "no lists",
        "paragraphs",
        "prose",
    ],
    fix="a list was asked for: answer in bullet points, not reflowed prose",
)


FormatTable = Lexicon(
    name="format_table",
    indicates=[
        "columns",
        "comparison table",
        "grid",
        "matrix",
        "rows",
        "side by side",
        "spreadsheet",
        "table",
        "tabular",
    ],
    fix="a table was asked for: lay the answer out in columns, not prose",
)


FormatCode = Lexicon(
    name="format_code",
    indicates=[
        "class",
        "cli",
        "code",
        "config",
        "function",
        "implementation",
        "json",
        "module",
        "query",
        "regex",
        "repo",
        "script",
        "snippet",
        "sql",
        "yaml",
    ],
    rules_out=[
        "conceptually",
        "don't write code",
        "explain only",
        "no code",
        "without code",
    ],
    fix="code was asked for: answer with the actual code, not a description of it",
)


FormatProse = Lexicon(
    name="format_prose",
    indicates=[
        "article",
        "essay",
        "flowing",
        "full sentences",
        "narrative",
        "no bullets",
        "no lists",
        "paragraphs",
        "prose",
        "write up",
    ],
    rules_out=[
        "bullet",
        "bullets",
        "list",
        "numbered",
        "table",
    ],
    fix="prose was asked for: write flowing paragraphs, not bullets or a table",
)


LengthShort = Lexicon(
    name="length_short",
    indicates=[
        "a few words",
        "brief",
        "briefly",
        "concise",
        "concisely",
        "in a nutshell",
        "keep it short",
        "no waffle",
        "one line",
        "one paragraph",
        "one sentence",
        "quick",
        "short",
        "shortly",
        "summarise",
        "summary",
        "terse",
        "tl;dr",
        "tldr",
    ],
    rules_out=[
        "at length",
        "comprehensive",
        "detailed",
        "exhaustive",
        "full",
        "in depth",
        "thorough",
    ],
    fix="brevity was asked for: cut to the answer and stop, don't chase completeness",
)


LengthLong = Lexicon(
    name="length_long",
    indicates=[
        "at length",
        "complete guide",
        "comprehensive",
        "deep dive",
        "detailed",
        "everything",
        "exhaustive",
        "expand on",
        "full breakdown",
        "in depth",
        "in detail",
        "thorough",
        "thoroughly",
    ],
    rules_out=[
        "brief",
        "concise",
        "keep it short",
        "one line",
        "one sentence",
        "short",
        "tldr",
    ],
    fix="depth was asked for: cover the ground fully; a terse answer underserves it",
)


NoPreamble = Lexicon(
    name="no_preamble",
    indicates=[
        "answer only",
        "don't explain",
        "get to the point",
        "just give me",
        "just the",
        "no explanation",
        "no intro",
        "no introduction",
        "no preamble",
        "nothing else",
        "output only",
        "skip the",
        "straight to",
    ],
    fix="no preamble was asked for: open on the answer itself",
)


NoCaveats = Lexicon(
    name="no_caveats",
    indicates=[
        "don't hedge",
        "don't lecture",
        "i know the risks",
        "i'm aware",
        "no caveats",
        "no disclaimers",
        "no hedging",
        "no need to warn",
        "no warnings",
        "skip the disclaimer",
        "spare me",
        "without the caveats",
    ],
    fix="caveats were waved off: drop the disclaimers, the risk is already accepted",
)


CitationDemand = Lexicon(
    name="citation_demand",
    indicates=[
        "according to what",
        "back it up",
        "citations",
        "cite",
        "evidence",
        "footnotes",
        "link to",
        "reference",
        "references",
        "show your sources",
        "where did you get",
        "with sources",
    ],
    rules_out=[
        "don't bother citing",
        "no sources needed",
        "off the top of your head",
    ],
    fix="sources were asked for: attach a citation to each actionable claim",
)


StepByStep = Lexicon(
    name="step_by_step",
    indicates=[
        "first steps",
        "guide",
        "how do i",
        "how to",
        "in order",
        "instructions",
        "one at a time",
        "procedure",
        "step by step",
        "tutorial",
        "walk me through",
    ],
    fix="a walkthrough was asked for: give numbered steps in order",
)


OpinionDemand = Lexicon(
    name="opinion_demand",
    indicates=[
        "best option",
        "do you reckon",
        "prefer",
        "recommend",
        "recommendation",
        "what do you think",
        "what would you do",
        "which should i",
        "would you",
        "your opinion",
        "your take",
        "your view",
    ],
    rules_out=[
        "don't editorialise",
        "just the facts",
        "no opinions",
        "objectively",
    ],
    fix="a recommendation was asked for: commit to a call, not a list of options",
)


ComparisonDemand = Lexicon(
    name="comparison_demand",
    indicates=[
        "against",
        "better than",
        "compare",
        "comparison",
        "difference between",
        "differences",
        "pros and cons",
        "trade offs",
        "tradeoffs",
        "versus",
        "vs",
        "which is",
    ],
    fix="a comparison was asked for: weigh them head to head on the axes that matter",
)


CreativeDemand = Lexicon(
    name="creative_demand",
    indicates=[
        "character",
        "creative",
        "fiction",
        "imagine",
        "in the style of",
        "invent",
        "lyrics",
        "make up",
        "plot",
        "poem",
        "riff on",
        "screenplay",
        "story",
    ],
    rules_out=[
        "accurate",
        "actual",
        "don't make anything up",
        "factual",
        "real",
    ],
    fix="creative work was asked for: invent freely, this is not a request for fact",
)


FactualDemand = Lexicon(
    name="factual_demand",
    indicates=[
        "accurate",
        "accurately",
        "actual",
        "actually",
        "correct",
        "don't make anything up",
        "exact",
        "facts",
        "factual",
        "no hallucination",
        "precisely",
        "real",
        "true",
        "verify",
    ],
    rules_out=[
        "creative",
        "fictional",
        "imagine",
        "invent",
        "made up",
        "story",
    ],
    fix="accuracy was asked for: stick to what you can verify and flag uncertainty",
)


RolePlay = Lexicon(
    name="role_play",
    indicates=[
        "act as",
        "imagine you're",
        "in character",
        "play the part",
        "pretend",
        "respond as",
        "role play",
        "roleplay",
        "take on the role",
        "you are a",
    ],
    fix="a role was asked for: stay in character, don't answer as the assistant",
)


Revision = Lexicon(
    name="revision",
    indicates=[
        "adjust",
        "again but",
        "another version",
        "change it",
        "different angle",
        "instead of",
        "longer",
        "make it",
        "punch it up",
        "redo",
        "revise",
        "rewrite",
        "shorter",
        "try again",
        "tweak",
    ],
    fix="a revision was asked for: rework the previous answer, don't start over",
)


AdviceDemand = Lexicon(
    name="advice_demand",
    indicates=[
        "advice",
        "advise",
        "dangerous",
        "do you think i",
        "help me decide",
        "is it legal",
        "is it safe",
        "is it worth",
        "my case",
        "my situation",
        "my symptoms",
        "risky",
        "should i",
        "what should",
        "worth doing",
    ],
    fix="advice was asked for: give a clear recommendation with reasoning and risks",
)


ToneFormal = Lexicon(
    name="tone_formal",
    indicates=[
        "academic",
        "business",
        "client facing",
        "corporate",
        "for publication",
        "formal",
        "official",
        "polished",
        "professional",
    ],
    rules_out=[
        "banter",
        "casual",
        "chatty",
        "informal",
        "relaxed",
    ],
    fix="a formal tone was asked for: write in a polished, professional register",
)


ToneCasual = Lexicon(
    name="tone_casual",
    indicates=[
        "casual",
        "chatty",
        "conversational",
        "friendly",
        "informal",
        "keep it human",
        "like a mate",
        "no jargon",
        "plain english",
        "relaxed",
    ],
    rules_out=[
        "academic",
        "corporate",
        "formal",
        "official",
        "professional",
    ],
    fix="a casual tone was asked for: write plainly, drop the corporate register",
)


__all__ = [
    "FormatList",
    "FormatTable",
    "FormatCode",
    "FormatProse",
    "LengthShort",
    "LengthLong",
    "NoPreamble",
    "NoCaveats",
    "CitationDemand",
    "StepByStep",
    "OpinionDemand",
    "ComparisonDemand",
    "CreativeDemand",
    "FactualDemand",
    "RolePlay",
    "Revision",
    "AdviceDemand",
    "ToneFormal",
    "ToneCasual",
]
