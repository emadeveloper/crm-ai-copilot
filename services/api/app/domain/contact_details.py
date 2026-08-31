"""The person behind a lead — mirrors the `contact` object in the lead-api payload."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.errors import ValidationError
from app.domain.value_objects import Email, blank_to_none


@dataclass(frozen=True, slots=True)
class ContactDetails:
    name: str
    email: Email
    company: str | None = None
    role: str | None = None
    message: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("contact name must not be blank")
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "company", blank_to_none(self.company))
        object.__setattr__(self, "role", blank_to_none(self.role))
        object.__setattr__(self, "message", blank_to_none(self.message))
