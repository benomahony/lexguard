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
    fix="add it to what needs buying",
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
    fix="reach out to the person named",
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
    fix="handle the payment or amount owed",
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
    fix="keep the appointment; mind when and where",
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
    fix="arrange or catch the trip on time",
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
    fix="handle it as part of your work",
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
    fix="get the chore done",
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
    fix="see to the pet's care",
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
    fix="see to the child's school or care need",
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
    fix="get the gardening done",
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
    fix="renew or service it before it lapses",
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
    fix="keep it to read or watch, don't act on it as a task",
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
    fix="prepare for it ahead of the date",
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
    fix="act on it where it happens",
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
    fix="involve the person named",
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
