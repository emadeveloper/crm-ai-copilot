"""Lead score: an integer 0..100, a band derived from it, and a short rationale."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.errors import InvalidScore

MIN_VALUE = 0
MAX_VALUE = 100
WARM_THRESHOLD = 40
HOT_THRESHOLD = 75


class ScoreBand(StrEnum):
    COLD = "cold"
    WARM = "warm"
    HOT = "hot"


def band_for_value(value: int) -> ScoreBand:
    """Canonical band for a score value. Cold 0-39, warm 40-74, hot 75-100."""
    if value >= HOT_THRESHOLD:
        return ScoreBand.HOT
    if value >= WARM_THRESHOLD:
        return ScoreBand.WARM
    return ScoreBand.COLD


@dataclass(frozen=True, slots=True)
class Score:
    value: int
    band: ScoreBand
    rationale: str

    def __post_init__(self) -> None:
        if not MIN_VALUE <= self.value <= MAX_VALUE:
            raise InvalidScore(f"score value {self.value} is outside {MIN_VALUE}..{MAX_VALUE}")
        if self.band is not band_for_value(self.value):
            raise InvalidScore(
                f"band {self.band} contradicts value {self.value} "
                f"(expected {band_for_value(self.value)})"
            )
        if not self.rationale.strip():
            raise InvalidScore("score rationale must not be blank")

    @classmethod
    def create(cls, value: int, rationale: str) -> Score:
        """Build a score, deriving the band from the value. Range is enforced in __post_init__."""
        return cls(value=value, band=band_for_value(value), rationale=rationale)
