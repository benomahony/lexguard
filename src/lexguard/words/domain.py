from __future__ import annotations

from ..lexicon import Lexicon

Shopping = Lexicon(
    name="shopping",
    indicates=[
        "add to basket",
        "buy",
        "get some",
        "grab",
        "groceries",
        "need more",
        "order",
        "out of",
        "pick up",
        "purchase",
        "restock",
        "run out",
        "shop",
        "shopping",
        "top up",
    ],
    fix="treat this as something to buy",
)


Communication = Lexicon(
    name="communication",
    indicates=[
        "call",
        "chase",
        "drop a line",
        "email",
        "follow up",
        "get back to",
        "let them know",
        "message",
        "phone",
        "reply",
        "respond",
        "ring",
        "tell",
        "text",
        "whatsapp",
    ],
    fix="treat this as a message to send someone",
)


Money = Lexicon(
    name="money",
    indicates=[
        "bill",
        "budget",
        "cost",
        "deposit",
        "direct debit",
        "expenses",
        "invoice",
        "owe",
        "owed",
        "pay",
        "payment",
        "refund",
        "reimburse",
        "renew",
        "standing order",
        "subscription",
        "top up",
        "transfer",
    ],
    fix="treat this as a payment or money matter",
)


HealthAppointment = Lexicon(
    name="health_appointment",
    indicates=[
        "appointment",
        "blood test",
        "check up",
        "clinic",
        "dental",
        "dentist",
        "doctor",
        "gp",
        "hospital",
        "jab",
        "optician",
        "physio",
        "prescription",
        "repeat prescription",
        "surgery",
        "vaccination",
    ],
    fix="treat this as a medical appointment to keep",
)


Travel = Lexicon(
    name="travel",
    indicates=[
        "airbnb",
        "boarding",
        "book travel",
        "car hire",
        "check in",
        "flight",
        "hotel",
        "itinerary",
        "mot",
        "parking",
        "passport",
        "petrol",
        "platform",
        "service",
        "taxi",
        "ticket",
        "train",
        "visa",
    ],
    fix="treat this as a trip to arrange or catch",
)


Work = Lexicon(
    name="work",
    indicates=[
        "appraisal",
        "deck",
        "deploy",
        "expenses",
        "incident",
        "oncall",
        "one to one",
        "pr",
        "pull request",
        "release",
        "report",
        "retro",
        "review",
        "rfc",
        "slides",
        "spec",
        "sprint",
        "standup",
        "ticket",
        "timesheet",
    ],
    fix="treat this as work, tracked with the rest of it",
)


Household = Lexicon(
    name="household",
    indicates=[
        "bedding",
        "bins",
        "bleed the radiators",
        "boiler",
        "dishwasher",
        "dusting",
        "hoover",
        "ironing",
        "laundry",
        "lightbulb",
        "recycling",
        "smoke alarm",
        "tidy",
        "vacuum",
        "washing",
    ],
    fix="treat this as a household chore",
)


Pets = Lexicon(
    name="pets",
    indicates=[
        "cat",
        "cattery",
        "dog",
        "feed the",
        "flea",
        "groomer",
        "kennels",
        "kitten",
        "litter tray",
        "pet food",
        "puppy",
        "vet",
        "walk the",
        "worming",
    ],
    fix="treat this as pet care",
)


Children = Lexicon(
    name="children",
    indicates=[
        "after school",
        "homework",
        "inset day",
        "nursery",
        "packed lunch",
        "parents evening",
        "pick up from school",
        "playdate",
        "school run",
        "swimming lesson",
        "term starts",
        "uniform",
    ],
    fix="treat this as a childcare or school matter",
)


Garden = Lexicon(
    name="garden",
    indicates=[
        "bird feeder",
        "compost",
        "garden",
        "greenhouse",
        "hedge",
        "lawn",
        "mow",
        "plant",
        "prune",
        "seeds",
        "water the plants",
        "weeding",
        "weeds",
    ],
    fix="treat this as a gardening task",
)


Maintenance = Lexicon(
    name="maintenance",
    indicates=[
        "boiler service",
        "expires",
        "gas safety",
        "insurance",
        "mot",
        "renew",
        "renewal",
        "road tax",
        "service",
        "subscription ends",
        "tv licence",
        "tyres",
        "warranty",
    ],
    fix="treat this as upkeep with a renewal or service date",
)


Media = Lexicon(
    name="media",
    indicates=[
        "album",
        "article",
        "book",
        "chapter",
        "episode",
        "film",
        "listen",
        "movie",
        "newsletter",
        "podcast",
        "read",
        "series",
        "video",
        "watch",
    ],
    fix="this is something to read or watch, not a task to do",
)


Occasion = Lexicon(
    name="occasion",
    indicates=[
        "anniversary",
        "bank holiday",
        "birthday",
        "bonfire night",
        "christmas",
        "easter",
        "father's day",
        "graduation",
        "halloween",
        "housewarming",
        "leaving do",
        "mother's day",
        "new year",
        "valentine",
        "wedding",
        "xmas",
    ],
    fix="treat this as an event with a date to prepare for",
)


Location = Lexicon(
    name="location",
    indicates=[
        "at",
        "chemist",
        "en route",
        "gym",
        "high street",
        "home",
        "near",
        "nearby",
        "office",
        "on the way",
        "pharmacy",
        "post office",
        "school",
        "shop",
        "shops",
        "station",
        "supermarket",
        "town",
        "while i'm",
        "work",
    ],
    fix="this is tied to a place; use where it happens",
)


People = Lexicon(
    name="people",
    indicates=[
        "boss",
        "brother",
        "catch up",
        "client",
        "colleague",
        "dad",
        "dentist",
        "doctor",
        "father",
        "husband",
        "landlord",
        "manager",
        "meet",
        "meeting",
        "mother",
        "mum",
        "neighbour",
        "partner",
        "see",
        "sister",
        "team",
        "vet",
        "visit",
        "wife",
        "with",
    ],
    fix="this involves a specific person; keep them attached",
)


__all__ = [
    "Shopping",
    "Communication",
    "Money",
    "HealthAppointment",
    "Travel",
    "Work",
    "Household",
    "Pets",
    "Children",
    "Garden",
    "Maintenance",
    "Media",
    "Occasion",
    "Location",
    "People",
]
