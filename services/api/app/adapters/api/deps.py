"""FastAPI dependency providers backed by the app's Container."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.application.get_lead import GetLead
from app.application.list_leads import ListLeads
from app.application.submit_lead import SubmitLead
from app.infra.container import Container


def get_container(request: Request) -> Container:
    container: Container = request.app.state.container
    return container


ContainerDep = Annotated[Container, Depends(get_container)]


def submit_lead_uc(container: ContainerDep) -> SubmitLead:
    return container.submit_lead()


def get_lead_uc(container: ContainerDep) -> GetLead:
    return container.get_lead()


def list_leads_uc(container: ContainerDep) -> ListLeads:
    return container.list_leads()
