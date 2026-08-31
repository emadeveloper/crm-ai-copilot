"""Mounts the GraphQL schema at ``/graphql`` with the app Container in context."""

from __future__ import annotations

from typing import Any

from fastapi import Request
from strawberry.fastapi import GraphQLRouter

from app.adapters.api.graphql.schema import schema


async def _get_context(request: Request) -> dict[str, Any]:
    return {"container": request.app.state.container}


graphql_router: GraphQLRouter[dict[str, Any], None] = GraphQLRouter(
    schema, path="/graphql", context_getter=_get_context
)
