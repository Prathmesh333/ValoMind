import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "workers/analysis"))

from valomind_video.context import clock_seconds, phase, team_side
from valomind_video.pov import propose_windows, write_table


def item(text, confidence=0.9, x=950, y=30):
    return {
        "text": text,
        "confidence": confidence,
        "x1": x - 20,
        "x2": x + 20,
        "y1": y - 5,
        "y2": y + 5,
        "frame_width": 1920,
        "frame_height": 1080,
    }


@pytest.mark.parametrize(
    ("text", "expected"), [("1:40", 100), ("1.30", 90), ("0:07", 7), ("1:99", None), ("100", None)]
)
def test_clock_parsing(text, expected):
    assert clock_seconds(text) == expected


def test_short_clocks_are_not_automatically_buy_phase():
    assert phase([item("0:20")], ["sidebar"])["phase"] == "unknown"
    assert phase([item("0:20")], ["buy"])["phase"] == "buy_phase_candidate"
    assert phase([item("0:20"), item("BUY PHASE")])["phase"] == "buy_phase"


def test_timeout_90_seconds_requires_marker_and_technical_precedence():
    assert phase([item("1:30")])["phase"] == "unknown"
    assert (
        phase([item("1:30"), item("TACTICAL TIMEOUT")], ["sidebar"])["phase"] == "tactical_timeout"
    )
    assert phase([item("1:30"), item("TECHNICAL TIMEOUT")])["phase"] == "technical_pause"


def test_live_candidate_requires_spatial_clock_round_and_layout():
    assert phase([item("1:30"), item("ROUND 3")], ["sidebar"])["phase"] == "active_round_candidate"
    assert phase([item("1:30", x=1700), item("ROUND 3")], ["sidebar"])["phase"] == "unknown"
    assert phase([item("1:30"), item("ROUND 3")], ["buy"])["phase"] == "unknown"


def test_replay_and_postplant_are_explicit_no_missing_clock_plant_guess():
    assert phase([item("SPIKE PLANTED")])["phase"] == "postplant"
    assert phase([item("REPLAY"), item("SPIKE PLANTED")])["phase"] == "replay"
    assert phase([item("ROUND 3")], ["sidebar"])["phase"] == "unknown"


def test_side_switch_uses_reviewed_team_mapping_and_overtime_is_explicit():
    assert team_side("a", 1, ["a", "b"]) == "unknown"
    assert team_side("a", 12, ["a", "b"], "a") == "attack"
    assert team_side("a", 13, ["a", "b"], "a") == "defense"
    assert team_side("a", 25, ["a", "b"], "a") == "unknown"
    assert team_side("a", 25, ["a", "b"], "a", "b") == "defense"
    assert team_side("a", 26, ["a", "b"], "a", "b") == "attack"


def test_window_selection_excludes_known_buy_and_timeout_centers(tmp_path):
    segments = [
        {"timestamp_ms": "6000", "segment_type": "gameplay", "processing_action": "extract"},
        {"timestamp_ms": "20000", "segment_type": "gameplay", "processing_action": "extract"},
        {"timestamp_ms": "40000", "segment_type": "gameplay", "processing_action": "extract"},
    ]
    source = write_table(tmp_path / "segments.csv", segments, list(segments[0]))
    context = [
        {"timestamp_ms": "6000", "phase": "buy_phase_candidate"},
        {"timestamp_ms": "20000", "phase": "tactical_timeout"},
        {"timestamp_ms": "40000", "phase": "active_round_candidate"},
    ]
    write_table(tmp_path / "round_context.csv", context, list(context[0]))
    assert propose_windows(source) == [{"start_seconds": 38.0, "end_seconds": 42.0}]
