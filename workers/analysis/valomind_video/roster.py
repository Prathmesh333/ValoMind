"""Spatial VCT roster proposals. No membership or pick is inferred from world labels."""

import csv
import hashlib
from collections import defaultdict
from pathlib import Path

from .entities import normalize

PROFILE_VERSION = "vct_1080_v3"
NAMES = [
    "Cryo",
    "bang",
    "Vora",
    "Asuna",
    "Timotino",
    "Chronicle",
    "Derke",
    "Jamppi",
    "Sayonara",
    "PROFEK",
]
# This seed is scoped to the inspected source; it is not a global player directory.
SOURCE_CATALOG = {
    "omjZXmc7_4A": {
        "players": {
            normalize(name): f"source_handle:omjZXmc7_4A:{normalize(name)}" for name in NAMES
        },
        "teams": {"100t": "100t", "i0ot": "100t", "10ot": "100t", "iqot": "100t", "vit": "vit"},
        "maps": {"split": "split", "summit": "summit", "lotus": "lotus"},
    }
}
ROSTER_FIELDS = [
    "roster_observation_id",
    "source_url",
    "video_id",
    "timestamp_ms",
    "frame_index",
    "map_id",
    "team_id",
    "opposing_team_id",
    "player_id",
    "display_name",
    "character_agent_id",
    "side",
    "slot",
    "layout",
    "name_confidence",
    "team_confidence",
    "map_confidence",
    "review_status",
    "evidence_observation_id",
    "portrait_x1",
    "portrait_y1",
    "portrait_x2",
    "portrait_y2",
    "profile_version",
]


def inside(row, region, width, height):
    x = (float(row["x1"]) + float(row["x2"])) / 2 * 1920 / width
    y = (float(row["y1"]) + float(row["y2"])) / 2 * 1080 / height
    x1, y1, x2, y2 = region
    return x1 <= x <= x2 and y1 <= y <= y2


def unique(candidates):
    """Conflicting OCR identities in one region require review, not a best guess."""
    if not candidates or len({value for value, _ in candidates}) != 1:
        return "", ""
    return candidates[0][0], max(confidence for _, confidence in candidates)


def parse_frame(rows, width=1920, height=1080, catalog=None):
    if width <= 0 or height <= 0:
        raise ValueError("Frame dimensions must be positive")
    if not rows:
        return []
    source = rows[0]["video_id"]
    catalog = catalog or SOURCE_CATALOG.get(source)
    if catalog is None:
        return []  # Unknown broadcast needs a reviewed catalog, not guessed identities.
    ocr = [row for row in rows if row["kind"] == "ocr"]
    teams = []
    for region in [(710, 0, 795, 55), (1125, 0, 1200, 55)]:
        candidates = [
            (catalog["teams"][normalize(row["text"])], float(row["confidence"]))
            for row in ocr
            if float(row["confidence"]) >= 0.2
            and normalize(row["text"]) in catalog["teams"]
            and inside(row, region, width, height)
        ]
        teams.append(unique(candidates))
    if teams[0][0] and teams[0][0] == teams[1][0]:
        teams = [("", ""), ("", "")]  # Two scoreboard sides cannot establish one team.
    maps = []
    for row in ocr:
        text = normalize(row["text"])
        if text.startswith("current ") and inside(row, (0, 0, 220, 35), width, height):
            name = text.removeprefix("current ")
            if name in catalog["maps"] and float(row["confidence"]) >= 0.5:
                maps.append((catalog["maps"][name], float(row["confidence"])))
    map_id, map_confidence = unique(maps)
    output = []
    for layout in ["buy", "sidebar"]:
        for side in range(2):
            for slot in range(5):
                if layout == "buy":
                    y = 783 + slot * 56
                    region = (645, y, 815, y + 53) if side == 0 else (1165, y, 1275, y + 53)
                    portrait = (573, y, 641, y + 53) if side == 0 else (1276, y, 1348, y + 53)
                else:
                    y = 550 + slot * 106
                    region = (77, y, 255, y + 45) if side == 0 else (1725, y, 1841, y + 45)
                    portrait = (17, y, 76, y + 47) if side == 0 else (1841, y, 1905, y + 47)
                candidates = [
                    row
                    for row in ocr
                    if normalize(row["text"]) in catalog["players"]
                    and float(row["confidence"]) >= 0.5
                    and inside(row, region, width, height)
                ]
                player, confidence = unique(
                    [
                        (catalog["players"][normalize(row["text"])], float(row["confidence"]))
                        for row in candidates
                    ]
                )
                if not player:
                    continue
                evidence = max(candidates, key=lambda row: float(row["confidence"]))
                identity = f"{evidence['observation_id']}:{PROFILE_VERSION}:{layout}:{side}:{slot}"
                row = {field: "" for field in ROSTER_FIELDS}
                row.update(
                    roster_observation_id=hashlib.sha256(identity.encode()).hexdigest()[:24],
                    source_url=evidence["source_url"],
                    video_id=source,
                    timestamp_ms=evidence["timestamp_ms"],
                    frame_index=evidence["frame_index"],
                    map_id=map_id,
                    map_confidence=map_confidence,
                    team_id=teams[side][0],
                    team_confidence=teams[side][1],
                    opposing_team_id=teams[1 - side][0],
                    player_id=player,
                    display_name=evidence["text"],
                    side=["left", "right"][side],
                    slot=slot + 1,
                    layout=layout,
                    name_confidence=confidence,
                    review_status="proposed",
                    evidence_observation_id=evidence["observation_id"],
                    profile_version=PROFILE_VERSION,
                )
                for field, value in zip(
                    ["portrait_x1", "portrait_y1", "portrait_x2", "portrait_y2"],
                    portrait,
                    strict=True,
                ):
                    row[field] = round(
                        value * (width / 1920 if field.endswith(("x1", "x2")) else height / 1080)
                    )
                output.append(row)
    # Two possible layouts or slots for one identity is ambiguous.
    counts = defaultdict(int)
    for row in output:
        counts[row["player_id"]] += 1
    return [row for row in output if counts[row["player_id"]] == 1]


def export_rosters(observations, output=None, width=1920, height=1080, catalog=None):
    groups = defaultdict(list)
    with Path(observations).open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row.get("processing_action") == "extract":
                groups[(row["video_id"], int(row["frame_index"]))].append(row)
    result = []
    for key in sorted(groups):
        group = groups[key]
        result.extend(
            parse_frame(
                group,
                width=int(group[0].get("frame_width") or width),
                height=int(group[0].get("frame_height") or height),
                catalog=catalog,
            )
        )
    target = Path(output) if output else Path(observations).with_name("roster_observations.csv")
    temp = target.with_suffix(".csv.tmp")
    with temp.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=ROSTER_FIELDS)
        writer.writeheader()
        writer.writerows(result)
    temp.replace(target)
    return target
