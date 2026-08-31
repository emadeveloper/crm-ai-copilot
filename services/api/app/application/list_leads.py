"""List leads for the dashboard queue, newest first, with a clamped page size."""

from __future__ import annotations

from app.domain.lead_aggregate import LeadAggregate
from app.domain.ports import LeadRepository

_DEFAULT_LIMIT = 20
_MAX_LIMIT = 100


class ListLeads:
    def __init__(
        self,
        *,
        leads: LeadRepository,
        default_limit: int = _DEFAULT_LIMIT,
        max_limit: int = _MAX_LIMIT,
    ) -> None:
        self._leads = leads
        self._default_limit = default_limit
        self._max_limit = max_limit

    async def execute(self, *, limit: int | None = None, offset: int = 0) -> list[LeadAggregate]:
        effective_limit = min(limit or self._default_limit, self._max_limit)
        effective_offset = max(offset, 0)
        return await self._leads.list_aggregates(limit=effective_limit, offset=effective_offset)
