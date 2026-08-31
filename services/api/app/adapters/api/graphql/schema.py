"""GraphQL query slice: ``lead(id)`` and ``leads(limit, offset)``, over the same use cases."""

from __future__ import annotations

from typing import Any

import strawberry

from app.adapters.api.graphql.types import Lead, lead_from_aggregate
from app.domain.errors import LeadNotFound
from app.domain.value_objects import LeadId
from app.infra.container import Container


def _container(info: strawberry.Info[dict[str, Any], Any]) -> Container:
    container: Container = info.context["container"]
    return container


@strawberry.type
class Query:
    @strawberry.field
    async def lead(self, info: strawberry.Info[dict[str, Any], Any], id: str) -> Lead | None:
        try:
            aggregate = await _container(info).get_lead().execute(LeadId.from_string(id))
        except (LeadNotFound, ValueError):
            return None
        return lead_from_aggregate(aggregate)

    @strawberry.field
    async def leads(
        self,
        info: strawberry.Info[dict[str, Any], Any],
        limit: int = 20,
        offset: int = 0,
    ) -> list[Lead]:
        aggregates = await _container(info).list_leads().execute(limit=limit, offset=offset)
        return [lead_from_aggregate(a) for a in aggregates]


schema = strawberry.Schema(query=Query)
