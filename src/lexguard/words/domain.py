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
    fix="add the item to the shopping list and note the quantity if one is given",
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
    fix="capture who to contact and on which channel, then draft or schedule the message",
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
    fix="log the amount, payee, and due date, and set a reminder before it falls due",
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
    fix="record the date, time, and location, and set a reminder to leave in good time",
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
    fix="capture the dates, booking reference, and departure time, and add reminders around them",
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
    fix="file the item under the right project and track its owner and deadline",
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
    fix="add the chore to the home list and set it to recur if it is routine",
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
    fix="schedule the pet task and set a recurring reminder for routine care",
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
    fix="add the school or childcare item to the family calendar with its date and any prep",
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
    fix="add the garden task and set it to recur with the season where relevant",
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
    fix="record the renewal or service date and set a reminder well before it expires",
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
    fix="save the title to the watch or read list rather than treating it as a task",
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
    fix="note the date, remind ahead of it, and capture any gift or booking to arrange",
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
    fix="attach the place to the task so it can surface when nearby or en route",
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
    fix="link the task to the named person so related items group together",
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
