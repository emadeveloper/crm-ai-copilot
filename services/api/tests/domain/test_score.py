"""Task 2.2 — Score value object (spec: ai-enrichment / score 0..100 <-> band)."""

from __future__ import annotations

import pytest

from app.domain.errors import InvalidScore
from app.domain.score import Score, ScoreBand, band_for_value


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, ScoreBand.COLD),
        (39, ScoreBand.COLD),
        (40, ScoreBand.WARM),
        (74, ScoreBand.WARM),
        (75, ScoreBand.HOT),
        (100, ScoreBand.HOT),
    ],
)
def test_band_for_value_maps_ranges(value: int, expected: ScoreBand) -> None:
    assert band_for_value(value) is expected


def test_score_keeps_a_consistent_value_band_and_rationale() -> None:
    score = Score(value=82, band=ScoreBand.HOT, rationale="Enterprise buyer, explicit budget")
    assert (score.value, score.band, score.rationale) == (
        82,
        ScoreBand.HOT,
        "Enterprise buyer, explicit budget",
    )


@pytest.mark.parametrize("value", [-1, 101, 140])
def test_score_rejects_values_outside_0_100(value: int) -> None:
    with pytest.raises(InvalidScore):
        Score(value=value, band=band_for_value(min(max(value, 0), 100)), rationale="x")


def test_score_rejects_a_band_that_contradicts_the_value() -> None:
    with pytest.raises(InvalidScore):
        Score(value=90, band=ScoreBand.COLD, rationale="mismatch")


def test_score_rejects_a_blank_rationale() -> None:
    with pytest.raises(InvalidScore):
        Score(value=50, band=ScoreBand.WARM, rationale="   ")


class TestScoreCreate:
    def test_derives_the_band_from_the_value(self) -> None:
        assert Score.create(30, "early-stage, no budget").band is ScoreBand.COLD
        assert Score.create(95, "perfect ICP match").band is ScoreBand.HOT

    def test_still_enforces_the_range(self) -> None:
        with pytest.raises(InvalidScore):
            Score.create(200, "too high")
