"""LLM-derived facts about a lead."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Enrichment:
    industry: str | None
    company_size_band: str | None
    seniority: str | None
    intent_signals: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        # Accept any iterable of signals; store an immutable tuple.
        object.__setattr__(self, "intent_signals", tuple(self.intent_signals))
