"""A drafted first-touch reply for a lead."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.errors import InvalidReplyDraft


@dataclass(frozen=True, slots=True)
class ReplyDraft:
    subject: str
    body: str

    def __post_init__(self) -> None:
        if not self.subject.strip():
            raise InvalidReplyDraft("reply draft subject must not be blank")
        if not self.body.strip():
            raise InvalidReplyDraft("reply draft body must not be blank")
