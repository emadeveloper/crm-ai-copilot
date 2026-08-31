"""Composition root: build adapters from settings and hand out wired use cases."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.adapters.crm.hubspot import HubSpotPrivateAppAdapter
from app.adapters.llm.gemini import GeminiAIStudioAdapter
from app.adapters.persistence.repository import SqlLeadRepository
from app.adapters.queue.postgres import PostgresTaskQueue
from app.application.enrich_lead import EnrichLead
from app.application.get_lead import GetLead
from app.application.list_leads import ListLeads
from app.application.submit_lead import SubmitLead
from app.application.sync_lead_to_crm import SyncLeadToCrm
from app.domain.ports import CrmGateway, LeadRepository, LLMProvider, TaskQueue
from app.infra.config import Settings
from app.infra.db import get_sessionmaker

_HUBSPOT_BASE_URL = "https://api.hubapi.com"


@dataclass(slots=True)
class Container:
    settings: Settings
    leads: LeadRepository
    queue: TaskQueue
    llm: LLMProvider
    crm: CrmGateway
    _closables: list[httpx.AsyncClient]

    @classmethod
    def from_settings(cls, settings: Settings) -> Container:  # pragma: no cover -- real wiring
        from google import genai  # noqa: PLC0415 -- optional heavy import, only for the real wiring

        sessionmaker = get_sessionmaker()
        http = httpx.AsyncClient(
            base_url=_HUBSPOT_BASE_URL,
            headers={"Authorization": f"Bearer {settings.hubspot_private_app_token}"},
            timeout=15.0,
        )
        genai_client = genai.Client(api_key=settings.gemini_api_key)
        return cls(
            settings=settings,
            leads=SqlLeadRepository(sessionmaker),
            queue=PostgresTaskQueue(sessionmaker),
            llm=GeminiAIStudioAdapter.from_client(
                genai_client,
                model=settings.llm_model,
                rate_per_min=settings.llm_rate_per_min,
            ),
            crm=HubSpotPrivateAppAdapter(http),
            _closables=[http],
        )

    # --- use case providers -------------------------------------------------

    def submit_lead(self) -> SubmitLead:
        return SubmitLead(leads=self.leads, queue=self.queue)

    def enrich_lead(self) -> EnrichLead:
        return EnrichLead(
            leads=self.leads,
            queue=self.queue,
            llm=self.llm,
            max_attempts=self.settings.max_task_attempts,
        )

    def sync_lead_to_crm(self) -> SyncLeadToCrm:
        return SyncLeadToCrm(leads=self.leads, crm=self.crm)

    def get_lead(self) -> GetLead:
        return GetLead(leads=self.leads)

    def list_leads(self) -> ListLeads:
        return ListLeads(leads=self.leads)

    async def aclose(self) -> None:
        for client in self._closables:
            await client.aclose()
