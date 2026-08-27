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
    fix="add the item to the shopping list with its quantity; don't lose it in a note",
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
    fix="capture who to contact and on which channel, then draft or schedule it",
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
    fix="capture the amount, payee, and due date and remind before it's due",
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
    fix="capture the date, time, and place, and remind in time to leave",
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
    fix="capture the dates, reference, and departure time, and remind around them",
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
    fix="file this under its project with an owner and a deadline",
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
    fix="add the chore to the home list and make it recur if it's routine",
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
    fix="schedule the pet task and make routine care recur",
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
    fix="put it on the family calendar with its date and any prep needed",
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
    fix="add the garden task and make it recur with the season where it applies",
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
    fix="capture the renewal or service date and remind well before it expires",
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
    fix="save the title to a watch or read list; don't action it as a task",
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
    fix="attach the place so the task surfaces when nearby or en route",
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
