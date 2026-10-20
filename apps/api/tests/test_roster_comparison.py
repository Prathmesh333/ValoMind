import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from compare_roster_reference import compare


def test_missing_and_unresolved_are_not_reported_as_wrong_predictions():
    reference = {
        "video_id": "synthetic",
        "timestamp_ms": "1000",
        "side": "left",
        "slot": "1",
        "display_name": "Alpha",
        "team_id": "t1",
        "map_id": "m1",
        "character_agent_id": "c1",
    }
    row = {**reference, "character_agent_id": "", "team_id": "wrong"}
    _, summary = compare([reference], [row])
    assert summary["fields"]["character_agent_id"] == {"unresolved": 1}
    assert summary["fields"]["team_id"] == {"mismatch": 1}
    _, missing = compare([reference], [])
    assert missing["fields"]["display_name"] == {"missing_row": 1}


def test_duplicate_reference_rejected_and_duplicate_predictions_exposed():
    row = {
        "video_id": "synthetic",
        "timestamp_ms": "1000",
        "side": "left",
        "slot": "1",
        "display_name": "Alpha",
        "team_id": "t1",
        "map_id": "m1",
        "character_agent_id": "c1",
    }
    with pytest.raises(ValueError):
        compare([row, row], [])
    results, _ = compare([row], [row, row])
    assert results[0]["pipeline_row_status"] == "conflicting"
