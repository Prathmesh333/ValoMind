"""Compare frame/slot reference annotations with exported roster proposals."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

FIELDS = ["display_name", "team_id", "map_id", "character_agent_id"]


def key(row):
    return row["video_id"], int(row["timestamp_ms"]), row["side"], int(row["slot"])


def compare(reference, predictions):
    lookup = defaultdict(list)
    for row in predictions:
        lookup[key(row)].append(row)
    if len({key(row) for row in reference}) != len(reference):
        raise ValueError("Duplicate reference frame/slot")
    results = []
    counts = {field: Counter() for field in FIELDS}
    for manual in reference:
        matches = lookup[key(manual)]
        auto = matches[0] if len(matches) == 1 else None
        row = {field: manual[field] for field in ["video_id", "timestamp_ms", "side", "slot"]}
        row["pipeline_row_status"] = (
            "present" if auto else ("conflicting" if matches else "missing")
        )
        for field in FIELDS:
            value = auto.get(field, "") if auto else ""
            status = (
                ("conflicting_rows" if len(matches) > 1 else "missing_row")
                if auto is None
                else (
                    "unresolved"
                    if not value
                    else (
                        "match" if value.casefold() == str(manual[field]).casefold() else "mismatch"
                    )
                )
            )
            row["manual_" + field] = manual[field]
            row["pipeline_" + field] = value
            row[field + "_status"] = status
            counts[field][status] += 1
        results.append(row)
    frames = {(row["video_id"], int(row["timestamp_ms"])) for row in reference}
    reference_keys = {key(row) for row in reference}
    extras = [
        row
        for row in predictions
        if (row["video_id"], int(row["timestamp_ms"])) in frames and key(row) not in reference_keys
    ]
    return results, {
        "scope": "Selected frames in the first 120 seconds; not full-video or blind evaluation",
        "reference_rows": len(reference),
        "reference_frames": len(frames),
        "pipeline_rows_present": sum(row["pipeline_row_status"] == "present" for row in results),
        "extra_pipeline_rows_in_reference_frames": len(extras),
        "fields": {field: dict(value) for field, value in counts.items()},
        "independent_review_status": "pending",
        "note": "Assistant visual annotations remain proposals, not independent verified ground truth.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("predictions", type=Path)
    args = parser.parse_args()
    with args.reference.open(newline="", encoding="utf-8") as stream:
        reference = list(csv.DictReader(stream))
    with args.predictions.open(newline="", encoding="utf-8") as stream:
        predictions = list(csv.DictReader(stream))
    result, summary = compare(reference, predictions)
    if not result:
        raise ValueError("Reference is empty")
    with args.reference.with_name("comparison.csv").open(
        "w", newline="", encoding="utf-8"
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=list(result[0]))
        writer.writeheader()
        writer.writerows(result)
    args.reference.with_name("summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
