"""Evaluate only explicitly reviewed segment samples; preserve abstention counts."""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def evaluate(rows):
    labels = {"gameplay", "roster", "filler", "replay", "uncertain"}
    reviewed = [
        row for row in rows if row.get("review_status") == "reviewed" and row.get("reviewer_id")
    ]
    if not reviewed:
        raise ValueError("No reviewed segment references")
    counts = Counter()
    misses = 0
    admitted_nonmatch = 0
    for row in reviewed:
        expected, actual = row["reference_segment"], row["suggested_segment"]
        if expected not in labels or actual not in labels:
            raise ValueError("Invalid segment class")
        counts[(expected, actual)] += 1
        misses += expected in {"gameplay", "roster"} and row["processing_action"] != "extract"
        admitted_nonmatch += (
            expected in {"filler", "replay"} and row["processing_action"] == "extract"
        )
    return {
        "reviewed_samples": len(reviewed),
        "matching_labels": sum(
            a == b
            for a, b in [(row["reference_segment"], row["suggested_segment"]) for row in reviewed]
        ),
        "missed_match_samples": misses,
        "admitted_filler_or_replay_samples": admitted_nonmatch,
        "confusion": [
            {"reference": a, "predicted": b, "count": count}
            for (a, b), count in sorted(counts.items())
        ],
        "scope": "Reviewed sampled frames only; no full-video accuracy claim",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review_csv", type=Path)
    args = parser.parse_args()
    with args.review_csv.open(newline="", encoding="utf-8") as stream:
        result = evaluate(list(csv.DictReader(stream)))
    output = args.review_csv.with_suffix(".evaluation.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
