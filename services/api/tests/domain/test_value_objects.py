"""Task 2.2 — value objects: LeadId, TaskId, Email, CrmContactId."""

from __future__ import annotations

from uuid import UUID

import pytest

from app.domain.errors import InvalidEmail
from app.domain.value_objects import CrmContactId, Email, LeadId, TaskId


class TestEmail:
    def test_accepts_and_returns_a_valid_address(self) -> None:
        assert Email("ada@example.com").value == "ada@example.com"

    def test_normalises_case_and_surrounding_whitespace(self) -> None:
        assert Email("  Ada@Example.COM  ").value == "ada@example.com"

    @pytest.mark.parametrize("raw", ["not-an-email", "ada@", "@example.com", "ada example.com", ""])
    def test_rejects_malformed_addresses(self, raw: str) -> None:
        with pytest.raises(InvalidEmail):
            Email(raw)

    def test_is_hashable_and_value_based(self) -> None:
        assert Email("a@b.com") == Email("A@B.COM")
        assert len({Email("a@b.com"), Email("a@b.com")}) == 1


class TestLeadId:
    def test_new_generates_a_unique_uuid(self) -> None:
        a, b = LeadId.new(), LeadId.new()
        assert isinstance(a.value, UUID)
        assert a != b

    def test_round_trips_through_string(self) -> None:
        original = LeadId.new()
        assert LeadId.from_string(str(original)) == original

    def test_from_string_rejects_non_uuid(self) -> None:
        with pytest.raises(ValueError):
            LeadId.from_string("nope")


class TestTaskId:
    def test_round_trips_through_string(self) -> None:
        original = TaskId.new()
        assert TaskId.from_string(str(original)) == original


class TestCrmContactId:
    def test_holds_a_non_empty_identifier(self) -> None:
        assert CrmContactId("101").value == "101"

    @pytest.mark.parametrize("raw", ["", "   "])
    def test_rejects_blank_identifiers(self, raw: str) -> None:
        with pytest.raises(ValueError):
            CrmContactId(raw)
