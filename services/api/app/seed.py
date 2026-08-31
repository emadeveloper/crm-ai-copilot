"""Seed the database with synthetic demo leads.

The deployed demo runs against the Gemini free tier, whose prompts may be used for training —
so every lead here is fictitious. Run with ``python -m app.seed`` or ``just seed``.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable, Mapping
from typing import Any

from app.application.submit_lead import SubmitLead, SubmitLeadCommand
from app.domain.contact_details import ContactDetails
from app.domain.value_objects import Email
from app.infra.config import get_settings
from app.infra.container import Container
from app.infra.logging import configure_logging

logger = logging.getLogger("app.seed")

SYNTHETIC_LEADS: list[dict[str, Any]] = [
    {
        "source": "website-form",
        "contact": {
            "name": "Ada Lovelace",
            "email": "ada@example.com",
            "company": "Analytical Engines",
            "role": "CTO",
            "message": "We're evaluating tools to score inbound leads for ~200 reps. Pricing?",
        },
    },
    {
        "source": "linkedin-ad",
        "contact": {
            "name": "Grace Hopper",
            "email": "grace@example.org",
            "company": "Navy Systems",
            "role": "VP Engineering",
            "message": "Interested in a demo next week.",
        },
    },
    {
        "source": "webinar",
        "contact": {
            "name": "Alan Turing",
            "email": "alan@example.com",
            "company": "Bletchley Ltd",
            "role": "Founder",
            "message": "Do you integrate with HubSpot? We already use it.",
        },
    },
    {
        "source": "referral",
        "contact": {
            "name": "Katherine Johnson",
            "email": "katherine@example.org",
            "company": "Orbital Mechanics Inc",
            "role": "Head of RevOps",
            "message": "A colleague recommended you. Looking to cut response time on trials.",
        },
    },
    {
        "source": "website-form",
        "contact": {
            "name": "Edsger",
            "email": "edsger@example.com",
            "message": "Just browsing, no budget yet.",
        },
    },
    {
        "source": "cold-inbound",
        "contact": {
            "name": "Margaret Hamilton",
            "email": "margaret@example.org",
            "company": "Apollo Guidance",
            "role": "Director of Software",
            "message": "Need something reliable. What are your uptime guarantees?",
        },
    },
    {
        "source": "website-form",
        "contact": {
            "name": "Barbara Liskov",
            "email": "barbara@example.com",
            "company": "Abstraction Labs",
            "role": "Principal Engineer",
            "message": "Evaluating three vendors. Send a comparison if you have one.",
        },
    },
    {
        "source": "conference",
        "contact": {
            "name": "Radia Perlman",
            "email": "radia@example.org",
            "company": "Spanning Tree Co",
            "role": "Fellow",
            "message": "Met you at the booth. Please follow up with next steps.",
        },
    },
]


async def seed_leads(
    submit: SubmitLead, leads: Iterable[Mapping[str, Any]] = SYNTHETIC_LEADS
) -> int:
    count = 0
    for raw in leads:
        contact = raw["contact"]
        await submit.execute(
            SubmitLeadCommand(
                source=raw["source"],
                contact=ContactDetails(
                    name=contact["name"],
                    email=Email(contact["email"]),
                    company=contact.get("company"),
                    role=contact.get("role"),
                    message=contact.get("message"),
                ),
            )
        )
        count += 1
    return count


async def _main() -> None:  # pragma: no cover -- CLI entrypoint, needs a live DB
    settings = get_settings()
    configure_logging(settings.log_level)
    container = Container.from_settings(settings)
    try:
        submitted = await seed_leads(container.submit_lead())
        logger.info("submitted %s synthetic leads", submitted)
    finally:
        await container.aclose()


if __name__ == "__main__":
    asyncio.run(_main())
