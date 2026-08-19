from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from pydantic_evals import Case, Dataset

from lexica import (
    AdviceDemand,
    Bloat,
    CitationDemand,
    CitationMarker,
    Confidential,
    Disclaimer,
    Lexicon,
    NoCaveats,
    Observe,
    Overclaim,
    Servility,
    Slop,
)


def under_test(agent: Agent[object, Any]):
    assert agent.model is not None, "the demo agent must have a model configured"
    assert agent.output_type is not None, "the demo agent must declare an output type"

    async def task(prompt: str):
        assert prompt, "task requires a non-empty prompt"
        output = (await agent.run(prompt)).output
        assert output is not None
        return output

    return task


def prose_gate() -> None:
    cases = [Case(name="explainer", inputs="explain database indexing")]
    assert cases
    agent = Agent(
        TestModel(
            custom_output_text=(
                "Great question! Let us delve into the intricate tapestry of "
                "indexing. Hope this helps!"
            )
        )
    )
    report = Dataset(
        name="prose_gate",
        cases=cases,
        evaluators=[Bloat.absent(), Servility.absent()],
    ).evaluate_sync(under_test(agent))
    assert len(report.cases) == len(cases)
    report.print(include_reasons=True)


def instruction_adherence() -> None:
    agent = Agent(
        TestModel(
            custom_output_text=(
                "Probably, though you should consult a professional before relying on it."
            )
        )
    )
    cases = [
        Case(
            name="opted_out",
            inputs="is this clause enforceable? no disclaimers, i know the risks",
        ),
        Case(name="definition", inputs="what is a tort"),
        Case(name="advice", inputs="should i sue my landlord over this clause"),
        Case(name="wants_sources", inputs="what caused the 2008 crash, with sources"),
    ]
    assert len(cases) == 4
    report = Dataset(
        name="instruction_adherence",
        cases=cases,
        evaluators=[
            Disclaimer.absent(when=NoCaveats),
            Disclaimer.absent(unless=AdviceDemand),
            CitationMarker.expected(when=CitationDemand),
        ],
    ).evaluate_sync(under_test(agent))
    assert len(report.cases) == len(cases)
    report.print(include_reasons=True)


Estimate = Lexicon(
    name="estimate",
    indicates=[
        "by end of sprint",
        "by friday",
        "delivery date",
        "eta",
        "man days",
        "next quarter",
        "next sprint",
        "roughly a week",
        "should take",
        "story points",
        "two weeks",
        "will take",
    ],
    rules_out=[
        "depends on",
        "hard to say",
        "no estimate",
        "unknown until",
        "we would need to spike",
    ],
    fix=(
        "do not put a duration on unscoped work; describe the next slice and "
        "what would reduce the uncertainty"
    ),
)

Certainty = Lexicon(
    name="certainty",
    indicates=[
        "drop in",
        "easy",
        "no problem",
        "out of the box",
        "plug and play",
        "should be fine",
        "simple",
        "straightforward",
        "trivial",
    ],
    rules_out=["depends", "several unknowns", "unclear", "we would need to check"],
    fix=(
        "name the unknown that makes it not simple; calling delivery work easy "
        "sets a commitment nobody agreed to"
    ),
)

Spike = Lexicon(
    name="spike",
    indicates=[
        "investigate first",
        "proof of concept",
        "prototype",
        "smallest thing",
        "spike",
        "thin slice",
        "timebox",
        "tracer bullet",
        "walking skeleton",
    ],
    fix="offer a bounded piece of discovery so the team learns something before committing",
)


def custom_domain() -> None:
    scoping = [Case(name="scoping", inputs="how long to migrate our auth service to OIDC?")]
    checks = [(Estimate | Certainty).absent(), Spike.expected()]
    replies = {
        "naive": (
            "That should take roughly a week, it is fairly straightforward, a simple drop in."
        ),
        "revised": (
            "It depends on how many clients hold their own session state. Start "
            "with a spike on the two noisiest consumers; that is the unknown "
            "that dominates everything after it."
        ),
    }
    assert len(replies) == 2
    for label, reply in replies.items():
        report = Dataset(
            name=f"custom_domain_{label}", cases=scoping, evaluators=checks
        ).evaluate_sync(under_test(Agent(TestModel(custom_output_text=reply))))
        assert len(report.cases) == len(scoping)
        report.print(include_reasons=True)


class Ticket(BaseModel):
    summary: str
    internal_notes: str = ""
    next_steps: list[str] = Field(default_factory=list)


def structured_output() -> None:
    agent = Agent(
        TestModel(
            custom_output_args={
                "summary": "Customer locked out of their account.",
                "internal_notes": "Their password is hunter2, reset it manually.",
                "next_steps": [
                    "Trigger a reset",
                    "This will definitely fix it, guaranteed",
                ],
            }
        ),
        output_type=Ticket,
    )
    assert agent.output_type is Ticket
    report = Dataset(
        name="structured_output",
        cases=[
            Case(
                name="ticket",
                inputs="customer cannot log in, they gave me their password over chat",
            )
        ],
        evaluators=[
            Confidential.absent(field="internal_notes"),
            Overclaim.absent(field="next_steps[]"),
        ],
    ).evaluate_sync(under_test(agent))
    assert len(report.cases) == 1
    report.print(include_reasons=True)


HouseStyle = Slop.extend(
    indicates=[
        "at this moment in time",
        "going forward",
        "in order to",
        "reach out",
        "utilise",
    ],
    fix="house style: prefer the shorter word, and never reach out when you can ask",
)


def house_style_and_shadow_mode() -> None:
    agent = Agent(
        TestModel(
            custom_output_text=(
                "Going forward we will utilise a new approach in order to unlock value."
            )
        )
    )
    cases = [Case(name="email", inputs="draft a note to the client about the delay")]
    assert cases
    gate_report = Dataset(
        name="house_style", cases=cases, evaluators=[HouseStyle.absent()]
    ).evaluate_sync(under_test(agent))
    assert len(gate_report.cases) == len(cases)
    gate_report.print(include_reasons=True)
    shadow_report = Dataset(
        name="shadow_mode", cases=cases, evaluators=[Observe([HouseStyle, Disclaimer])]
    ).evaluate_sync(under_test(agent))
    assert len(shadow_report.cases) == len(cases)
    shadow_report.print()


if __name__ == "__main__":
    prose_gate()
    instruction_adherence()
    custom_domain()
    structured_output()
    house_style_and_shadow_mode()
