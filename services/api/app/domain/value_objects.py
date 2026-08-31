"""Immutable value objects shared across the domain."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Self
from uuid import UUID, uuid4

from app.domain.errors import InvalidEmail

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def blank_to_none(text: str | None) -> str | None:
    """Trim ``text``; return ``None`` when it is missing or all whitespace."""
    if text is None:
        return None
    stripped = text.strip()
    return stripped or None


@dataclass(frozen=True, slots=True)
class _UuidId:
    """Base for UUID-backed identifiers. Subclasses are distinct types."""

    value: UUID

    @classmethod
    def new(cls) -> Self:
        return cls(uuid4())

    @classmethod
    def from_string(cls, raw: str) -> Self:
        return cls(UUID(raw))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class LeadId(_UuidId):
    pass


@dataclass(frozen=True, slots=True)
class TaskId(_UuidId):
    pass


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        normalised = self.value.strip().lower()
        if not _EMAIL_RE.match(normalised):
            raise InvalidEmail(self.value)
        object.__setattr__(self, "value", normalised)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class CrmContactId:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("CrmContactId must not be blank")

    def __str__(self) -> str:
        return self.value
