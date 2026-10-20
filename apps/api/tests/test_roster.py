import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "workers/analysis"))

from valomind_video.roster import parse_frame

CATALOG = {
    "players": {"alpha": "p1"},
    "teams": {"blue": "t1", "red": "t2"},
    "maps": {"arena": "m1", "other": "m2"},
}


def ocr(text, x, y, confidence=0.9, **kwargs):
    return {
        "observation_id": text,
        "video_id": "synthetic",
        "source_url": "synthetic://demo",
        "timestamp_ms": "1000",
        "frame_index": "60",
        "kind": "ocr",
        "text": text,
        "confidence": confidence,
        "x1": x,
        "y1": y,
        "x2": x + 10,
        "y2": y + 10,
        **kwargs,
    }


def test_row_assignment_and_current_map_only():
    rows = [
        ocr("Blue", 730, 10),
        ocr("Red", 1150, 10),
        ocr("CURRENT: Arena", 30, 1),
        ocr("NEXT: Other", 250, 1),
        ocr("Alpha", 80, 560),
        ocr("Alpha", 490, 890),
    ]
    result = parse_frame(rows, catalog=CATALOG)
    assert len(result) == 1
    assert result[0]["player_id"] == "p1"
    assert result[0]["team_id"] == "t1"
    assert result[0]["opposing_team_id"] == "t2"
    assert result[0]["map_id"] == "m1"
    assert result[0]["character_agent_id"] == ""
    assert result[0]["review_status"] == "proposed"


def test_unknown_team_not_carried_or_inferred_from_player():
    result = parse_frame([ocr("Alpha", 80, 560)], catalog=CATALOG)
    assert result[0]["team_id"] == ""
    assert result[0]["map_id"] == ""


def test_conflicting_team_abstains():
    rows = [ocr("Blue", 730, 10), ocr("Red", 730, 10), ocr("Alpha", 80, 560)]
    assert parse_frame(rows, catalog=CATALOG)[0]["team_id"] == ""


def test_same_team_on_both_scoreboard_sides_is_not_assigned():
    rows = [ocr("Blue", 730, 10), ocr("Blue", 1150, 10), ocr("Alpha", 80, 560)]
    result = parse_frame(rows, catalog=CATALOG)
    assert result[0]["team_id"] == ""
    assert result[0]["opposing_team_id"] == ""


def test_buy_layout_and_scaled_coordinates():
    rows = [ocr("Alpha", 650 / 2, 795 / 2)]
    result = parse_frame(rows, width=960, height=540, catalog=CATALOG)
    assert result[0]["layout"] == "buy"
    assert result[0]["portrait_x1"] == round(573 / 2)


def test_unknown_source_does_not_get_test_video_catalog():
    assert parse_frame([ocr("Cryo", 80, 560)]) == []


def test_player_on_both_sides_abstains():
    rows = [ocr("Alpha", 80, 560), ocr("Alpha", 1750, 560)]
    assert parse_frame(rows, catalog=CATALOG) == []


def test_inspected_team_alias_is_spatially_scoped():
    rows = [ocr("IQOT", 730, 10, confidence=0.38), ocr("VIT", 1150, 10), ocr("Cryo", 80, 560)]
    for row in rows:
        row["video_id"] = "omjZXmc7_4A"
    assert parse_frame(rows)[0]["team_id"] == "100t"
    rows[0].update(x1=300, x2=310, y1=300, y2=310)
    assert parse_frame(rows)[0]["team_id"] == ""
