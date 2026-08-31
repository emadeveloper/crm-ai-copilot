"""Phase 3 refactor — ContactDetails value object (mirrors the lead-api payload `contact`)."""

from __future__ import annotations

import pytest

from app.domain.contact_details import ContactDetails
from app.domain.errors import InvalidEmail, ValidationError
from app.domain.value_objects import Email


def test_holds_required_and_optional_fields() -> None:
    contact = ContactDetails(
        name="Ada Lovelace",
        email=Email("ada@example.com"),
        company="Analytical Engines",
        role="CTO",
        message="Interested in a demo",
    )
    assert contact.name == "Ada Lovelace"
    assert contact.email == Email("ada@example.com")
    assert contact.company == "Analytical Engines"
    assert contact.role == "CTO"
    assert contact.message == "Interested in a demo"


def test_optionals_default_to_none() -> None:
    contact = ContactDetails(name="Ada", email=Email("ada@example.com"))
    assert (contact.company, contact.role, contact.message) == (None, None, None)


def test_trims_text_and_collapses_blank_optionals_to_none() -> None:
    contact = ContactDetails(
        name="  Ada Lovelace  ",
        email=Email("ada@example.com"),
        company="   ",
        message="  hi  ",
    )
    assert contact.name == "Ada Lovelace"
    assert contact.company is None
    assert contact.message == "hi"


def test_rejects_blank_name() -> None:
    with pytest.raises(ValidationError):
        ContactDetails(name="   ", email=Email("ada@example.com"))


def test_email_must_already_be_a_value_object() -> None:
    # The Email VO does its own validation; a bad address never reaches ContactDetails.
    with pytest.raises(InvalidEmail):
        ContactDetails(name="Ada", email=Email("nope"))
