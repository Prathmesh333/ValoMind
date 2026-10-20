"""Retry only unresolved roster fields, preserving all original OCR evidence."""

from collections import Counter

from .roster import parse_frame

RETRY_VERSION = "crop_retry_v1"


def retry_regions(rows, width, height, catalog=None):
    roster = parse_frame(rows, width, height, catalog)
    regions = []
    for side, box in [("left", (710, 0, 795, 55)), ("right", (1125, 0, 1200, 55))]:
        if not any(row["side"] == side and row["team_id"] for row in roster):
            regions.append(("team", box))
    layouts = Counter(row["layout"] for row in roster)
    # Do not select a layout when both plausible layouts have recognized names.
    if len(layouts) == 1 and next(iter(layouts.values())) >= 3:
        layout = next(iter(layouts))
        existing = {(row["side"], row["slot"]) for row in roster}
        for side in ["left", "right"]:
            for slot in range(1, 6):
                if (side, slot) in existing:
                    continue
                if layout == "buy":
                    y = 783 + (slot - 1) * 56
                    box = (645, y, 815, y + 53) if side == "left" else (1165, y, 1275, y + 53)
                else:
                    y = 550 + (slot - 1) * 106
                    box = (77, y, 255, y + 45) if side == "left" else (1725, y, 1841, y + 45)
                regions.append(("player_name", box))
    return [
        (
            kind,
            tuple(
                round(value * (width / 1920 if i % 2 == 0 else height / 1080))
                for i, value in enumerate(box)
            ),
        )
        for kind, box in regions
    ]


def retry(frame, reader, rows, catalog=None):
    import cv2

    height, width = frame.shape[:2]
    output = []
    for kind, (x1, y1, x2, y2) in retry_regions(rows, width, height, catalog):
        crop = frame[y1:y2, x1:x2]
        enlarged = cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        for box, text, confidence in reader.readtext(enlarged):
            xs, ys = zip(*box, strict=True)
            output.append(
                {
                    "kind": "ocr",
                    "label": f"retry.{kind}",
                    "text": text,
                    "confidence": float(confidence),
                    "x1": x1 + min(xs) / 3,
                    "y1": y1 + min(ys) / 3,
                    "x2": x1 + max(xs) / 3,
                    "y2": y1 + max(ys) / 3,
                }
            )
    return output
