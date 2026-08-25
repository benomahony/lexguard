from __future__ import annotations

from ..lexicon import Lexicon

Preamble = Lexicon(
    name="preamble",
    indicates=[
        "absolutely",
        "as you requested",
        "before we dive in",
        "certainly",
        "glad to",
        "happy to",
        "here is a",
        "here's a",
        "here's the",
        "i'd be happy",
        "i'll start by",
        "i've put together",
        "in this response",
        "let me",
        "of course",
        "sure",
        "to answer your question",
    ],
    fix=("drop the opener and start with the answer; the first sentence should carry information"),
)


Postamble = Lexicon(
    name="postamble",
    indicates=[
        "anything else",
        "don't hesitate",
        "feel free to",
        "happy to adjust",
        "hope that helps",
        "hope this helps",
        "i can also",
        "i hope this",
        "if you'd like",
        "in summary",
        "just say the word",
        "let me know if",
        "overall",
        "to summarise",
        "would you like me to",
    ],
    fix=(
        "end on the last substantive sentence; offers to help further belong in the "
        "interface, not the text"
    ),
)


Sycophancy = Lexicon(
    name="sycophancy",
    indicates=[
        "astute",
        "brilliant question",
        "excellent point",
        "excellent question",
        "fantastic",
        "good catch",
        "good question",
        "great point",
        "great question",
        "i love this",
        "insightful",
        "smart approach",
        "spot on",
        "that's a really",
        "what a great",
        "you're absolutely right",
        "you're right",
    ],
    fix="delete the compliment; it adds no information and reads as flattery",
    source="Sharma et al. 2023",
)


Hedging = Lexicon(
    name="hedging",
    indicates=[
        "apparently",
        "appears to",
        "arguably",
        "broadly speaking",
        "conceivably",
        "could potentially",
        "for the most part",
        "generally",
        "in general",
        "in many ways",
        "in some cases",
        "it depends",
        "likely",
        "may",
        "might",
        "more or less",
        "often",
        "perhaps",
        "plausibly",
        "possibly",
        "presumably",
        "probably",
        "relatively",
        "seems",
        "somewhat",
        "tends to",
        "to some extent",
        "typically",
        "usually",
    ],
    rules_out=[
        "certainly",
        "definitely",
        "guaranteed",
        "i could be wrong",
        "i don't know",
        "i'm not sure",
        "no doubt",
        "uncertain",
        "undoubtedly",
    ],
    fix=(
        "commit to a claim or say plainly that you do not know; stacked qualifiers are not "
        "calibration"
    ),
    source="Lakoff 1973; Hyland 2005 (hedges); CoNLL-2010 uncertainty cues",
)


Overclaim = Lexicon(
    name="overclaim",
    indicates=[
        "100%",
        "always",
        "beyond doubt",
        "bulletproof",
        "cannot fail",
        "certainly",
        "certainly will",
        "clearly",
        "completely safe",
        "definitely",
        "definitely will",
        "foolproof",
        "guaranteed",
        "guarantees",
        "indisputably",
        "never fails",
        "no doubt",
        "no risk",
        "obviously",
        "perfect solution",
        "proven to",
        "the best",
        "the only",
        "undeniably",
        "undoubtedly",
        "unequivocally",
        "unquestionably",
        "without a doubt",
        "without question",
    ],
    rules_out=[
        "depends",
        "in some cases",
        "may",
        "might",
        "typically",
    ],
    fix=(
        "state the condition under which the claim holds, or downgrade it to what the "
        "evidence supports"
    ),
    source="Hyland 2005 (boosters)",
)


Disclaimer = Lexicon(
    name="disclaimer",
    indicates=[
        "consult a professional",
        "consult a qualified",
        "do your own research",
        "for informational purposes",
        "i'm not a doctor",
        "i'm not a lawyer",
        "not a substitute",
        "not financial advice",
        "not legal advice",
        "not medical advice",
        "seek professional",
        "speak to a",
        "this is general",
        "your mileage may vary",
    ],
    fix="only warn when the user is about to act on the answer, and say it once",
)


Refusal = Lexicon(
    name="refusal",
    indicates=[
        "against my guidelines",
        "i am unable",
        "i can't",
        "i cannot",
        "i don't feel comfortable",
        "i must decline",
        "i will not",
        "i won't",
        "i'd rather not",
        "i'm not able",
        "i'm unable",
        "not able to",
        "not something i can",
        "outside my",
    ],
    fix="if declining, give the reason and the nearest thing you can do instead",
)


SelfReference = Lexicon(
    name="self_reference",
    indicates=[
        "as a language model",
        "as an ai",
        "i don't have access",
        "i don't have the ability",
        "i was trained",
        "i'm just a",
        "i'm only able",
        "large language model",
        "my capabilities",
        "my knowledge cutoff",
        "my training",
        "my training data",
    ],
    fix=(
        "answer as the assistant, not about the assistant; model architecture is rarely the "
        "question"
    ),
)


Anthropomorphic = Lexicon(
    name="anthropomorphic",
    indicates=[
        "i enjoy",
        "i feel",
        "i felt",
        "i love",
        "i prefer",
        "i'm delighted",
        "i'm excited",
        "i'm passionate",
        "i'm sorry to hear",
        "i'm thrilled",
        "it makes me",
        "my favourite",
        "personally i",
    ],
    fix="describe the reasoning, not a feeling about it",
)


Slop = Lexicon(
    name="slop",
    indicates=[
        "at the end of the day",
        "beacon",
        "bedrock",
        "best-in-class",
        "cornerstone",
        "crucial",
        "cutting-edge",
        "deep dive",
        "delve",
        "delving",
        "dive deep",
        "elevate",
        "embark",
        "ever-changing",
        "ever-evolving",
        "game changer",
        "game-changer",
        "harness",
        "holistic",
        "in today's fast-paced",
        "intricacies",
        "intricate",
        "journey",
        "landscape",
        "leverage",
        "leveraging",
        "meticulous",
        "meticulously",
        "multifaceted",
        "myriad",
        "navigate the complexities",
        "nuanced",
        "paradigm",
        "pivotal",
        "plethora",
        "profound",
        "realm",
        "robust",
        "seamless",
        "seamlessly",
        "showcase",
        "showcasing",
        "state-of-the-art",
        "synergy",
        "tapestry",
        "testament",
        "transformative",
        "underpin",
        "underpins",
        "underscore",
        "underscores",
        "unlock",
        "unlocking",
        "unparalleled",
        "unwavering",
        "world-class",
    ],
    fix="swap for a plain verb or noun, or add these to the sampler ban list",
    source="Kobak et al. 2024 (excess vocabulary); slop-forensics",
)


TransitionSlop = Lexicon(
    name="transition_slop",
    indicates=[
        "additionally",
        "as mentioned",
        "bear in mind",
        "consequently",
        "furthermore",
        "hence",
        "importantly",
        "in addition",
        "in conclusion",
        "it is important to note",
        "it is worth noting",
        "it's important to note",
        "it's worth noting",
        "keep in mind",
        "moreover",
        "notably",
        "remember that",
        "significantly",
        "that said",
        "therefore",
        "thus",
        "to conclude",
    ],
    fix=("cut the connective; if the link between paragraphs needs stating, restructure instead"),
)


ContrastCliche = Lexicon(
    name="contrast_cliche",
    indicates=[
        "but rather",
        "enter the",
        "imagine if",
        "is not merely",
        "isn't merely",
        "it's less about",
        "it's not about",
        "more than just",
        "not just",
        "rather it's",
        "that's where",
        "the real question",
        "think of it as",
        "this is where",
    ],
    fix="make the positive claim directly rather than defining it against a strawman",
)


EmptyIntensifier = Lexicon(
    name="empty_intensifier",
    indicates=[
        "absolutely",
        "completely",
        "deeply",
        "enormously",
        "entirely",
        "exceptionally",
        "extremely",
        "genuinely",
        "highly",
        "hugely",
        "immensely",
        "incredibly",
        "massively",
        "profoundly",
        "quite",
        "quite literally",
        "really",
        "remarkably",
        "simply put",
        "terribly",
        "thoroughly",
        "totally",
        "tremendously",
        "truly",
        "utterly",
        "vastly",
        "very",
        "wholly",
    ],
    fix="delete the intensifier or replace it with the specific magnitude",
    source="Quirk et al. 1985; Biber et al. 1999 (amplifiers)",
)


UnsourcedAuthority = Lexicon(
    name="unsourced_authority",
    indicates=[
        "common knowledge",
        "critics say",
        "data suggests",
        "evidence shows",
        "experts agree",
        "experts say",
        "it has been claimed",
        "it is believed",
        "it is said",
        "it is thought",
        "it is widely",
        "it's well established",
        "many argue",
        "many believe",
        "reportedly",
        "research indicates",
        "research shows",
        "science says",
        "some argue",
        "some say",
        "sources say",
        "studies have shown",
        "studies show",
        "widely known",
        "widely regarded",
    ],
    fix="name the source or drop the appeal; vague authority is worse than no authority",
    source="Ganter & Strube 2009; Recasens et al. 2013 (weasel words)",
)


Apology = Lexicon(
    name="apology",
    indicates=[
        "apologies for",
        "i apologise",
        "i apologize",
        "i should have",
        "i was wrong",
        "let me correct",
        "my apologies",
        "my mistake",
        "sorry about",
        "sorry for the",
        "you're right i",
    ],
    fix="correct the error and move on; repeated apology shifts work onto the reader",
)


UncertaintyAdmission = Lexicon(
    name="uncertainty_admission",
    indicates=[
        "i am not sure",
        "i can't be certain",
        "i could be wrong",
        "i don't know",
        "i may be misremembering",
        "i'd need to check",
        "i'm not sure",
        "i'm uncertain",
        "without checking",
        "worth verifying",
    ],
    fix="say what you are unsure about and what would resolve it",
    source="CoNLL-2010 uncertainty cues",
)


SystemLeak = Lexicon(
    name="system_leak",
    indicates=[
        "i was told to",
        "my configuration",
        "my directive",
        "my instructions",
        "my rules",
        "my system prompt",
        "per my instructions",
        "the guidelines say",
        "the prompt says",
    ],
    fix="never surface configuration; answer within it",
)


EngagementBait = Lexicon(
    name="engagement_bait",
    indicates=[
        "buckle up",
        "but wait",
        "here's the fun part",
        "here's the kicker",
        "let's dive in",
        "let's explore",
        "ready?",
        "spoiler",
        "the best part is",
        "the exciting part",
        "you might be wondering",
    ],
    fix="cut the tease and lead with the substance",
)


Padding = Lexicon(
    name="padding",
    indicates=[
        "as you know",
        "at its core",
        "basically",
        "clearly",
        "essentially",
        "fundamentally",
        "in essence",
        "in other words",
        "needless to say",
        "obviously",
        "of course",
        "put simply",
        "simply put",
        "that is to say",
    ],
    fix="delete the phrase; if the point needs restating the first statement was unclear",
)


CitationMarker = Lexicon(
    name="citation_marker",
    indicates=[
        "according to",
        "cited",
        "doi",
        "https",
        "per the",
        "published in",
        "reference",
        "references",
        "reported by",
        "see",
        "source",
        "sources",
    ],
    fix="attach a source to each factual claim the user could act on",
)


__all__ = [
    "Preamble",
    "Postamble",
    "Sycophancy",
    "Hedging",
    "Overclaim",
    "Disclaimer",
    "Refusal",
    "SelfReference",
    "Anthropomorphic",
    "Slop",
    "TransitionSlop",
    "ContrastCliche",
    "EmptyIntensifier",
    "UnsourcedAuthority",
    "Apology",
    "UncertaintyAdmission",
    "SystemLeak",
    "EngagementBait",
    "Padding",
    "CitationMarker",
]
