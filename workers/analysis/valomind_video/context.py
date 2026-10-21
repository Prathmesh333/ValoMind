"""Versioned HUD phase proposals; clocks and display colors are not ground truth."""

import json
import re
from collections import defaultdict
from pathlib import Path

from .pov import read_table, write_table

VERSION = "hud_context_v1"
LIVE_ROUND_SECONDS = 100


def clock_seconds(text):
    match = re.fullmatch(r"(\d{1,2})[:.](\d{2})", text.strip())
    if not match or int(match[2]) >= 60:
        return None
    return int(match[1]) * 60 + int(match[2])


def phase(items, layouts=(), broadcast_state="gameplay"):
    """Never classify a short countdown, or the string 1:30, by value alone."""
    central, texts = [], []
    rounds = set()
    for item in items:
        confidence = float(item.get("confidence") or 0)
        text = item.get("text", "").strip().casefold()
        if confidence >= 0.5:
            texts.append(text)
        width, height = float(item.get("frame_width") or 0), float(item.get("frame_height") or 0)
        if width <= 0 or height <= 0:
            continue
        x = (float(item.get("x1") or 0) + float(item.get("x2") or 0)) / 2 / width
        y = (float(item.get("y1") or 0) + float(item.get("y2") or 0)) / 2 / height
        if not (0.4 <= x <= 0.6 and 0 <= y <= 0.10):
            continue
        seconds = clock_seconds(text)
        if seconds is not None and confidence >= 0.3:
            central.append(seconds)
        round_match = re.fullmatch(r"round\s*(\d{1,2})", text)
        if round_match and confidence >= 0.2 and int(round_match[1]) > 0:
            rounds.add(int(round_match[1]))
    clocks = set(central)
    seconds = next(iter(clocks)) if len(clocks) == 1 else None
    round_number = next(iter(rounds)) if len(rounds) == 1 else ""
    combined = " ".join(texts)
    label, reason = "unknown", "Insufficient phase evidence; no state carried over a highlight cut"
    if re.search(r"\breplay\b", combined) or broadcast_state == "replay":
        label, reason = "replay", "Replay marker or segment decision"
    elif re.search(
        r"\b(technical pause|tech pause|technical time ?out|tech time ?out)\b", combined
    ):
        label, reason = "technical_pause", "Explicit technical-pause marker"
    elif re.search(r"\b(tactical (?:time ?out|pause)|time ?out)\b", combined):
        label, reason = (
            "tactical_timeout",
            "Explicit timeout marker; duration not inferred from the countdown",
        )
    elif re.search(r"\b(match paused|game paused|halftime|half time)\b", combined):
        label, reason = "pause_or_halftime", "Explicit pause/halftime marker"
    elif re.search(r"\b(buy phase|purchase phase)\b", combined):
        label, reason = "buy_phase", "Explicit buy-phase text"
    elif re.search(r"\b(spike planted)\b", combined):
        label, reason = "postplant", "Explicit spike-planted text; plant timestamp unknown"
    elif re.search(r"\b(round won|round lost|flawless|thrifty|ace|team ace)\b", combined):
        label, reason = "round_end_candidate", "Round-result text; verify result overlay"
    elif broadcast_state not in {"gameplay", "unfiltered"}:
        reason = "No admitted match HUD; do not infer phase from off-game clocks"
    elif len(clocks) > 1:
        reason = "Conflicting central clocks"
    elif seconds is not None and 0 < seconds <= 45 and set(layouts) == {"buy"}:
        label, reason = (
            "buy_phase_candidate",
            "Short central countdown and buy-layout roster; barrier/text review still needed",
        )
    elif (
        seconds is not None
        and 45 < seconds <= LIVE_ROUND_SECONDS
        and set(layouts) == {"sidebar"}
        and round_number
    ):
        label, reason = (
            "active_round_candidate",
            "Long round clock, central round label and sidebar HUD; unseen pause remains possible",
        )
    elif seconds is not None and seconds <= LIVE_ROUND_SECONDS:
        reason = "Countdown alone cannot separate buy, live, pause and result phases"
    return {
        "phase": label,
        "reason": reason,
        "clock_seconds": seconds if seconds is not None else "",
        "round_number": round_number,
        "review_status": "proposed",
        "rule_version": VERSION,
    }


def team_side(
    team_id, round_number, team_ids, first_attacking_team=None, overtime_first_attacking_team=None
):
    """Use reviewed starting sides, never HUD colors or screen left/right."""
    if (
        len(team_ids) != 2
        or len(set(team_ids)) != 2
        or team_id not in team_ids
        or not isinstance(round_number, int)
        or isinstance(round_number, bool)
        or round_number < 1
    ):
        return "unknown"
    if round_number <= 24:
        initial = first_attacking_team
        swap = round_number > 12
    else:
        initial = overtime_first_attacking_team
        swap = (round_number - 25) % 2 == 1
    if initial not in team_ids:
        return "unknown"
    attacker = next(team for team in team_ids if team != initial) if swap else initial
    return "attack" if team_id == attacker else "defense"


def export_context(observations_csv, segments_csv, roster_csv):
    observations, layouts = defaultdict(list), defaultdict(set)
    for row in read_table(observations_csv):
        if row["kind"] == "ocr":
            observations[row["timestamp_ms"]].append(row)
    for row in read_table(roster_csv):
        layouts[row["timestamp_ms"]].add(row["layout"])
    rows = []
    for segment in read_table(segments_csv):
        stamp = segment["timestamp_ms"]
        result = phase(observations[stamp], layouts[stamp], segment["segment_type"])
        rows.append(
            dict(
                video_id=segment["video_id"],
                source_sha256=segment["source_sha256"],
                timestamp_ms=stamp,
                frame_index=segment["frame_index"],
                **result,
            )
        )
    fields = [
        "video_id",
        "source_sha256",
        "timestamp_ms",
        "frame_index",
        "phase",
        "reason",
        "clock_seconds",
        "round_number",
        "review_status",
        "rule_version",
    ]
    return write_table(Path(observations_csv).with_name("round_context.csv"), rows, fields)


def export_minimap_review(segments_csv):
    """Save review-only crops for the inspected source layout, not player tracks."""
    from PIL import Image

    path = Path(segments_csv)
    rows = []
    for segment in read_table(path):
        if segment["video_id"] != "omjZXmc7_4A":
            continue  # Other broadcasts require their own reviewed crop profile.
        details = json.loads(segment["text"])
        relative = details.get("review_image")
        if not relative:
            continue
        source = (path.parent / relative).resolve()
        if not source.is_relative_to(path.parent.resolve()) or not source.is_file():
            continue
        target = path.parent / "minimap_review" / f"frame_{segment['frame_index']}.jpg"
        target.parent.mkdir(exist_ok=True)
        with Image.open(source) as image:
            width, height = image.size
            box = (0, round(height * 0.04), round(width * 0.24), round(height * 0.36))
            image.crop(box).save(target, quality=95)
        rows.append(
            {
                "video_id": segment["video_id"],
                "source_sha256": segment["source_sha256"],
                "timestamp_ms": segment["timestamp_ms"],
                "image": str(target.relative_to(path.parent)).replace("\\", "/"),
                "crop_profile": "inspected_vct_1080_minimap_v1",
                "crop_review_status": "proposed",
                "map_id": "",
                "player_id": "",
                "team_id": "",
                "tactical_side": "unknown",
                "marker_x_normalized": "",
                "marker_y_normalized": "",
                "map_region": "",
                "world_x": "",
                "world_y": "",
                "player_visibility": "unknown",
                "reviewer_id": "",
                "notes": "Inspect map presence and crop; no marker detector or identity assignment",
            }
        )
    fields = list(rows[0]) if rows else ["video_id", "timestamp_ms", "image", "crop_review_status"]
    return write_table(path.with_name("minimap_review_suggestions.csv"), rows, fields)
