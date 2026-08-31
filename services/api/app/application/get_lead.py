"""Read a single lead with all of its derived data."""

from __future__ import annotations

from app.domain.errors import LeadNotFound
from app.domain.lead_aggregate import LeadAggregate
from app.domain.ports import LeadRepository
from app.domain.value_objects import LeadId


class GetLead:
    def __init__(self, *, leads: LeadRepository) -> None:
        self._leads = leads

    async def execute(self, lead_id: LeadId) -> LeadAggregate:
        aggregate = await self._leads.get_aggregate(lead_id)
        if aggregate is None:
            raise LeadNotFound(str(lead_id))
        return aggregate
