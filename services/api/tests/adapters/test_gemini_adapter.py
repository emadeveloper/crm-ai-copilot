"""Task 4.3 — GeminiAIStudioAdapter (seam-injected, no network)."""

from __future__ import annotations

import json

import pytest
from aiolimiter import AsyncLimiter

from app.adapters.llm.gemini import GeminiAIStudioAdapter, build_prompt, parse_analysis
from app.application.errors import LLMResponseInvalid, LLMTemporaryError
from app.domain.contact_details import ContactDetails
from app.domain.lead import Lead
from app.domain.score import ScoreBand
from app.domain.value_objects import Email

VALID_PAYLOAD = {
    "enrichment": {
        "industry": "fintech",
        "company_size_band": "51-200",
        "seniority": "c-level",
        "intent_signals": ["asked about pricing"],
    },
    "score": {"value": 82, "rationale": "Enterprise buyer with explicit budget"},
    "reply": {"subject": "Thanks for reaching out", "body": "Hi Ada, happy to help..."},
}


def _lead(message: str = "We need pricing for 200 seats") -> Lead:
    return Lead.register(
        source="website-form",
        contact=ContactDetails(
            name="Ada Lovelace",
            email=Email("ada@example.com"),
            company="Analytical Engines",
            message=message,
        ),
    )


class _CountingLimiter:
    def __init__(self) -> None:
        self.entered = 0

    async def __aenter__(self) -> None:
        self.entered += 1

    async def __aexit__(self, *exc: object) -> None:
        return None


def test_build_prompt_includes_lead_context() -> None:
    prompt = build_prompt(_lead(message="urgent: 200 seats"))
    assert "Ada Lovelace" in prompt
    assert "Analytical Engines" in prompt
    assert "200 seats" in prompt


class TestParseAnalysis:
    def test_maps_a_valid_payload_and_derives_the_band(self) -> None:
        analysis = parse_analysis(json.dumps(VALID_PAYLOAD))
        assert analysis.enrichment.industry == "fintech"
        assert analysis.enrichment.intent_signals == ("asked about pricing",)
        assert analysis.score.value == 82
        assert analysis.score.band is ScoreBand.HOT  # derived, not taken from the model
        assert analysis.reply_draft.subject == "Thanks for reaching out"

    def test_derives_a_cold_band_for_a_low_score(self) -> None:
        payload = {**VALID_PAYLOAD, "score": {"value": 15, "rationale": "no budget, students"}}
        assert parse_analysis(json.dumps(payload)).score.band is ScoreBand.COLD

    def test_rejects_non_json(self) -> None:
        with pytest.raises(LLMResponseInvalid):
            parse_analysis("not json at all")

    def test_rejects_a_missing_section(self) -> None:
        payload = {"enrichment": VALID_PAYLOAD["enrichment"], "reply": VALID_PAYLOAD["reply"]}
        with pytest.raises(LLMResponseInvalid):
            parse_analysis(json.dumps(payload))

    def test_rejects_an_out_of_range_score(self) -> None:
        payload = {**VALID_PAYLOAD, "score": {"value": 140, "rationale": "way too high"}}
        with pytest.raises(LLMResponseInvalid):
            parse_analysis(json.dumps(payload))

    def test_rejects_an_empty_reply_body(self) -> None:
        payload = {**VALID_PAYLOAD, "reply": {"subject": "Hi", "body": "   "}}
        with pytest.raises(LLMResponseInvalid):
            parse_analysis(json.dumps(payload))


class TestAnalyze:
    async def test_happy_path_calls_the_model_through_the_limiter(self) -> None:
        limiter = _CountingLimiter()
        calls: list[str] = []

        async def fake_generate(prompt: str) -> str:
            calls.append(prompt)
            return json.dumps(VALID_PAYLOAD)

        adapter = GeminiAIStudioAdapter(generate=fake_generate, limiter=limiter)
        analysis = await adapter.analyze(_lead())

        assert analysis.score.value == 82
        assert limiter.entered == 1
        assert len(calls) == 1

    async def test_transport_failure_becomes_a_temporary_error(self) -> None:
        async def boom(prompt: str) -> str:
            raise RuntimeError("connection reset")

        adapter = GeminiAIStudioAdapter(generate=boom, limiter=_CountingLimiter())
        with pytest.raises(LLMTemporaryError):
            await adapter.analyze(_lead())

    async def test_invalid_model_output_is_not_reported_as_temporary(self) -> None:
        async def bad_json(prompt: str) -> str:
            return "{ this is not valid"

        adapter = GeminiAIStudioAdapter(generate=bad_json, limiter=_CountingLimiter())
        with pytest.raises(LLMResponseInvalid):
            await adapter.analyze(_lead())

    def test_from_client_throttles_at_the_configured_per_minute_budget(self) -> None:
        # Burst protection (spec: lead-pipeline) is delegated to an AsyncLimiter sized to the
        # free-tier budget. `from_client` only stores the client, so a stub is enough here.
        adapter = GeminiAIStudioAdapter.from_client(
            object(),  # type: ignore[arg-type]
            model="gemini-3.6-flash",
            rate_per_min=15,
        )
        limiter = adapter._limiter
        assert isinstance(limiter, AsyncLimiter)
        assert (limiter.max_rate, limiter.time_period) == (15, 60)
