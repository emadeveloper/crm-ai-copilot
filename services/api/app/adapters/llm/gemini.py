"""``LLMProvider`` backed by the Google Gemini API (AI Studio free tier).

The adapter's job is narrow: throttle requests (``aiolimiter``), call the model asking for a
structured JSON reply, and translate outcomes into the application's error vocabulary. Retry and
backoff belong to the ``EnrichLead`` use case, not here — one source of retry truth.

Free-tier note: prompts may be used by Google for training. Only synthetic lead data is sent from
the deployed demo (see the seed script and README).
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager, nullcontext
from typing import TYPE_CHECKING, Any

from aiolimiter import AsyncLimiter

from app.application.errors import LLMResponseInvalid, LLMTemporaryError
from app.domain.enrichment import Enrichment
from app.domain.errors import ValidationError
from app.domain.lead import Lead
from app.domain.ports import LeadAnalysis
from app.domain.reply_draft import ReplyDraft
from app.domain.score import Score

if TYPE_CHECKING:
    from google import genai

Generate = Callable[[str], Awaitable[str]]
Limiter = AbstractAsyncContextManager[Any]

RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["enrichment", "score", "reply"],
    "properties": {
        "enrichment": {
            "type": "object",
            "properties": {
                "industry": {"type": "string", "nullable": True},
                "company_size_band": {"type": "string", "nullable": True},
                "seniority": {"type": "string", "nullable": True},
                "intent_signals": {"type": "array", "items": {"type": "string"}},
            },
        },
        "score": {
            "type": "object",
            "required": ["value", "rationale"],
            "properties": {
                "value": {"type": "integer"},
                "rationale": {"type": "string"},
            },
        },
        "reply": {
            "type": "object",
            "required": ["subject", "body"],
            "properties": {"subject": {"type": "string"}, "body": {"type": "string"}},
        },
    },
}


def build_prompt(lead: Lead) -> str:
    c = lead.contact
    return (
        "You qualify inbound sales leads. Given the lead below, return JSON matching the schema: "
        "an enrichment object (industry, company_size_band, seniority, intent_signals), a score "
        "(value 0-100 for fit/intent, and a one-sentence rationale), and a reply (a short, "
        "professional first-touch email with subject and body that references the "
        "lead's message).\n\n"
        f"Name: {c.name}\n"
        f"Email: {c.email}\n"
        f"Company: {c.company or 'unknown'}\n"
        f"Role: {c.role or 'unknown'}\n"
        f"Source: {lead.source}\n"
        f"Message: {c.message or '(none)'}\n"
    )


def parse_analysis(raw: str) -> LeadAnalysis:
    try:
        data = json.loads(raw)
        enrichment_data = data["enrichment"]
        score_data = data["score"]
        reply_data = data["reply"]
        analysis = LeadAnalysis(
            enrichment=Enrichment(
                industry=enrichment_data.get("industry"),
                company_size_band=enrichment_data.get("company_size_band"),
                seniority=enrichment_data.get("seniority"),
                intent_signals=tuple(enrichment_data.get("intent_signals") or ()),
            ),
            score=Score.create(int(score_data["value"]), str(score_data["rationale"])),
            reply_draft=ReplyDraft(
                subject=str(reply_data["subject"]), body=str(reply_data["body"])
            ),
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError, ValidationError) as exc:
        raise LLMResponseInvalid(f"could not parse Gemini response: {exc}") from exc
    return analysis


class GeminiAIStudioAdapter:
    def __init__(self, *, generate: Generate, limiter: Limiter | None = None) -> None:
        self._generate = generate
        self._limiter: Limiter = limiter if limiter is not None else nullcontext()

    @classmethod
    def from_client(
        cls, client: genai.Client, *, model: str, rate_per_min: int
    ) -> GeminiAIStudioAdapter:
        return cls(
            generate=gemini_generate(client, model),
            limiter=AsyncLimiter(rate_per_min, 60),
        )

    async def analyze(self, lead: Lead) -> LeadAnalysis:
        async with self._limiter:
            try:
                raw = await self._generate(build_prompt(lead))
            except LLMResponseInvalid:
                raise
            except Exception as exc:  # transport / SDK / rate-limit failure
                raise LLMTemporaryError(f"Gemini request failed: {exc}") from exc
        return parse_analysis(raw)


def gemini_generate(client: genai.Client, model: str) -> Generate:  # pragma: no cover
    """Wrap the google-genai async client as a plain ``prompt -> json string`` callable.

    The adapter's logic (throttle, parse, error-translate) is unit-tested via an injected
    ``generate``; this thin SDK binding is exercised only by the Phase 8 live smoke.
    """

    async def _generate(prompt: str) -> str:
        response = await client.aio.models.generate_content(
            model=model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": RESPONSE_SCHEMA,
            },
        )
        text = response.text
        if not text:
            raise LLMTemporaryError("Gemini returned an empty response")
        return text

    return _generate
