import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from audit_roster_export import audit


def test_audit_exposes_missing_slots_and_unknown_fields():
    rows = [
        {
            "video_id": "synthetic",
            "frame_index": "1",
            "timestamp_ms": "1000",
            "side": "left",
            "slot": "1",
            "player_id": "p1",
            "team_id": "",
            "character_agent_id": "",
            "map_id": "map1",
        }
    ]
    result = audit(rows)
    assert result["unknown_team_rows"] == 1
    assert result["unknown_agent_rows"] == 1
    assert len(result["incomplete_frames"][0]["missing_slots"]) == 9
    assert result["conflicting_frames"] == []


def test_audit_flags_duplicate_slot_and_player():
    row = {
        "video_id": "synthetic",
        "frame_index": "1",
        "timestamp_ms": "1000",
        "side": "left",
        "slot": "1",
        "player_id": "p1",
        "team_id": "t1",
        "character_agent_id": "",
        "map_id": "map1",
    }
    assert len(audit([row, dict(row)])["conflicting_frames"]) == 1
