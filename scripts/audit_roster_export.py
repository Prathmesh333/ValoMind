"""Audit a roster CSV without treating proposals as verified match data."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


def audit(rows):
    frames = defaultdict(list)
    for row in rows:
        frames[(row["video_id"], row["frame_index"])].append(row)
    missing = []
    conflicts = []
    for (video, frame), group in frames.items():
        slots = {(row["side"], int(row["slot"])) for row in group}
        absent = [
            (side, slot)
            for side in ["left", "right"]
            for slot in range(1, 6)
            if (side, slot) not in slots
        ]
        if absent:
            missing.append(
                {
                    "video_id": video,
                    "frame_index": frame,
                    "timestamp_ms": group[0]["timestamp_ms"],
                    "missing_slots": absent,
                }
            )
        if len(slots) != len(group) or len({row["player_id"] for row in group}) != len(group):
            conflicts.append({"video_id": video, "frame_index": frame})
    return {
        "rows": len(rows),
        "frames": len(frames),
        "display_handles": len({row["player_id"] for row in rows}),
        "unknown_team_rows": sum(not row["team_id"] for row in rows),
        "unknown_agent_rows": sum(not row["character_agent_id"] for row in rows),
        "map_counts": dict(Counter(row["map_id"] for row in rows)),
        "incomplete_frames": missing,
        "conflicting_frames": conflicts,
        "status": "Proposal coverage audit; not measured extraction accuracy",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    args = parser.parse_args()
    with args.csv.open(newline="", encoding="utf-8") as stream:
        result = audit(list(csv.DictReader(stream)))
    target = args.csv.with_name("roster_audit.json")
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
