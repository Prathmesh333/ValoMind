"""Conservative broadcast rules; unknown layouts remain reviewable, never guessed."""

import csv
import json
import re
from pathlib import Path

RULE_VERSION = "hud_rules_v3"


def export_review_queue(segment_csv):
    path = Path(segment_csv)
    fields = [
        "video_id",
        "timestamp_ms",
        "image",
        "suggested_segment",
        "processing_action",
        "reason",
        "reference_segment",
        "review_status",
        "reviewer_id",
    ]
    # Reviewers copy this generated file to segment_review_labels.csv before editing.
    target = path.with_name("segment_review_suggestions.csv")
    temporary = target.with_suffix(".csv.tmp")
    with (
        path.open(newline="", encoding="utf-8") as source,
        temporary.open("w", newline="", encoding="utf-8") as dest,
    ):
        writer = csv.DictWriter(dest, fieldnames=fields)
        writer.writeheader()
        for row in csv.DictReader(source):
            details = json.loads(row["text"])
            if details.get("review_image"):
                writer.writerow(
                    {
                        "video_id": row["video_id"],
                        "timestamp_ms": row["timestamp_ms"],
                        "image": details["review_image"],
                        "suggested_segment": row["segment_type"],
                        "processing_action": row["processing_action"],
                        "reason": details["reason"],
                        "reference_segment": "",
                        "review_status": "pending",
                        "reviewer_id": "",
                    }
                )
    temporary.replace(target)
    return target


def classify(texts):
    """Use a small upper-HUD OCR probe, not a full-frame detector, on every sample."""
    tokens = [text.strip().casefold() for text in texts]
    combined = " ".join(tokens)
    if re.search(r"\breplay\b", combined):
        return "replay", "Replay marker visible"
    if re.search(r"\b(starting lineup|agent select|map veto|map pick|team roster)\b", combined):
        return "roster", "Roster or selection marker visible"
    if re.search(
        r"\b(be right back|we.?ll be right back|starting soon|stream starting|"
        r"technical pause|halftime|half time|match paused|commercial break|"
        r"analyst desk|up next|stay tuned|intermission)\b",
        combined,
    ):
        return "filler", "Break, desk or pause marker visible"
    timer = any(re.fullmatch(r"\d{1,2}[:.]\d{2}", text) for text in tokens)
    # VCT's map-order strip and round label remain visible when score OCR fails.
    round_label = bool(re.search(r"\bround\s*\d{1,2}\b", combined))
    map_order = bool(re.search(r"\bcurrent\s*[:.]\s*\w+", combined)) and bool(
        re.search(r"\bnext\s*[:.]\s*\w+", combined)
    )
    if round_label and map_order:
        return "gameplay", "VCT map-order strip and round label visible"
    scores = sum(bool(re.fullmatch(r"\d{1,2}", text)) for text in tokens)
    if timer and scores >= 2:
        return "gameplay", "Upper HUD timer and two score candidates visible"
    return "uncertain", "No reliable broadcast-state signal"


def classify_probe(items, width, height):
    """Strong same-frame HUD groups can confirm a cut without carrying old state."""
    candidate, reason = classify([item["text"] for item in items if item["confidence"] >= 0.3])
    if candidate in {"filler", "replay", "roster"}:
        return candidate, reason, False

    def located(item, area):
        if not all(key in item for key in ["x1", "y1", "x2", "y2"]):
            return True  # Legacy upper-HUD transcripts: usable only for diagnostic replay.
        x = (item["x1"] + item["x2"]) / 2 / width
        y = (item["y1"] + item["y2"]) / 2 / height
        x1, y1, x2, y2 = area
        return x1 <= x <= x2 and y1 <= y <= y2

    map_text = [
        item["text"].strip().casefold()
        for item in items
        if item["confidence"] >= 0.5 and located(item, (0, 0, 0.34, 0.06))
    ]
    map_order = any(re.match(r"current\s*[:.]\s*\w+", text) for text in map_text) and any(
        re.match(r"next\s*[:.]\s*\w+", text) for text in map_text
    )
    clock = False
    round_label = False
    for item in items:
        text = item["text"].strip().casefold()
        if not located(item, (0.40, 0, 0.60, 0.10)):
            continue
        match = re.fullmatch(r"\d{1,2}[:.](\d{2})", text)
        clock |= bool(match and int(match[1]) < 60 and item["confidence"] >= 0.5)
        round_label |= bool(re.fullmatch(r"round\s*\d{1,2}", text) and item["confidence"] >= 0.2)
    if map_order and (clock or round_label):
        return "gameplay", "Same-frame map strip and central clock/round HUD", True
    return candidate, reason, False


class SegmentGate:
    """Confirm transitions across samples; suppress extraction during ambiguity."""

    def __init__(self, confirm_samples=2):
        if (
            not isinstance(confirm_samples, int)
            or isinstance(confirm_samples, bool)
            or confirm_samples < 1
        ):
            raise ValueError("confirm_samples must be a positive integer")
        self.required = confirm_samples
        self.state = {"stable": "uncertain", "candidate": "uncertain", "count": 0}

    def update(self, candidate, strong=False):
        if candidate not in {"gameplay", "roster", "replay", "filler", "uncertain"}:
            raise ValueError("Unknown segment type")
        count = self.state["count"] + 1 if candidate == self.state["candidate"] else 1
        stable = candidate if count >= self.required else self.state["stable"]
        if strong and candidate == "gameplay":
            stable = candidate
            count = max(count, self.required)
        self.state = {"stable": stable, "candidate": candidate, "count": count}
        # A previously stable match must not admit the first frame of an ad/replay.
        if candidate in {"replay", "filler"}:
            return candidate, "skip"
        if candidate in {"gameplay", "roster"} and stable == candidate and count >= self.required:
            return candidate, "extract"
        return "uncertain", "review"

    def restore(self, state):
        self.state = dict(state)
