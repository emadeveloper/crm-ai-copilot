"""REST endpoints for submitting and reading leads."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.adapters.api.deps import get_lead_uc, list_leads_uc, submit_lead_uc
from app.adapters.api.rest.schemas import LeadCreatedOut, LeadIn, LeadOut
from app.application.get_lead import GetLead
from app.application.list_leads import ListLeads
from app.application.submit_lead import SubmitLead, SubmitLeadCommand
from app.domain.contact_details import ContactDetails
from app.domain.errors import LeadNotFound, ValidationError
from app.domain.value_objects import Email, LeadId

router = APIRouter(prefix="/leads", tags=["leads"])


def _to_command(body: LeadIn) -> SubmitLeadCommand:
    try:
        contact = ContactDetails(
            name=body.contact.name,
            email=Email(body.contact.email),
            company=body.contact.company,
            role=body.contact.role,
            message=body.contact.message,
        )
    except ValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    return SubmitLeadCommand(source=body.source, contact=contact)


@router.post("", response_model=LeadCreatedOut)
async def create_lead(
    body: LeadIn,
    response: Response,
    submit: SubmitLead = Depends(submit_lead_uc),  # noqa: B008
) -> LeadCreatedOut:
    result = await submit.execute(_to_command(body))
    response.status_code = status.HTTP_200_OK if result.deduplicated else status.HTTP_201_CREATED
    return LeadCreatedOut(id=str(result.lead_id), deduplicated=result.deduplicated)


@router.get("", response_model=list[LeadOut])
async def list_leads(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    use_case: ListLeads = Depends(list_leads_uc),  # noqa: B008
) -> list[LeadOut]:
    aggregates = await use_case.execute(limit=limit, offset=offset)
    return [LeadOut.from_aggregate(a) for a in aggregates]


@router.get("/{lead_id}", response_model=LeadOut)
async def get_lead(
    lead_id: str,
    use_case: GetLead = Depends(get_lead_uc),  # noqa: B008
) -> LeadOut:
    try:
        aggregate = await use_case.execute(LeadId.from_string(lead_id))
    except (LeadNotFound, ValueError) as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="lead not found") from exc
    return LeadOut.from_aggregate(aggregate)
