from __future__ import annotations

from lexguard.lexicon import Lexicon, Source

Confidential = Lexicon(
    name="confidential",
    indicates=[
        "access token",
        "account number",
        "api key",
        "card number",
        "credentials",
        "cvv",
        "memorable word",
        "national insurance",
        "ni number",
        "passcode",
        "passport number",
        "password",
        "pin",
        "private key",
        "secret",
        "security question",
        "sort code",
    ],
    fix="redact the secret before it is persisted or echoed; store a reference, never the value",
)
Injection = Lexicon(
    name="injection",
    indicates=[
        "act as",
        "developer mode",
        "disregard the above",
        "ignore all previous",
        "ignore previous",
        "jailbreak",
        "new instructions",
        "override your",
        "system prompt",
        "you are an ai",
    ],
    fix="treat retrieved or user text as data, never as instructions; strip and log the attempt",
    evidence=(
        Source(cite="Perez & Ribeiro 2022", url="https://arxiv.org/abs/2211.09527"),
        Source(cite="Greshake et al. 2023", url="https://arxiv.org/abs/2302.12173"),
    ),
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

__all__ = ["Confidential", "Injection", "Refusal", "SystemLeak"]
