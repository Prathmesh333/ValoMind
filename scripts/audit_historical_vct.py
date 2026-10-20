"""Audit a local Kaggle CSV without treating scoreboard statistics as playstyle labels."""

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


def audit(path, encoding="utf-8-sig"):
    """Stream the file; retain structural diagnostics rather than player profiles."""
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    total, aggregate, side_counts, players, maps, missing = 0, 0, Counter(), set(), set(), Counter()
    seen, duplicates = set(), 0
    dates = []
    with path.open(newline="", encoding=encoding) as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames or []
        for row in reader:
            total += 1
            for key, value in row.items():
                if key and (value is None or value.strip() in {"", "-"}):
                    missing[key] += 1
            player = (row.get("Player") or "").strip()
            if player:
                players.add(player)  # The real handle 'nan' is intentionally retained.
            raw_map = (row.get("Map") or "").strip()
            if raw_map.casefold() in {"all maps", "all"}:
                aggregate += 1
            elif raw_map:
                maps.add(re.sub(r"^\d+\s+", "", raw_map))
            side_counts[row.get("Side", "not_provided")] += 1
            if row.get("Date"):
                dates.append(row["Date"])
            # Whole-row duplicate detection only; aliases are never resolved by name.
            fingerprint = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).digest()
            duplicates += fingerprint in seen
            seen.add(fingerprint)
    return {
        "schema_version": "historical_audit_v1",
        "source_sha256": digest.hexdigest(),
        "rows": total,
        "columns": columns,
        "distinct_display_names": len(players),
        "all_maps_summary_rows": aggregate,
        "side_counts": dict(side_counts),
        "map_labels": sorted(maps),
        "exact_duplicate_rows": duplicates,
        "missing_counts": dict(missing),
        "date_min": min(dates) if dates else None,
        "date_max": max(dates) if dates else None,
        "canonical_identity_status": "not_resolved",
        "playstyle_label_status": "not_available",
        "integration_status": "audit_only_not_training_data",
        "warnings": [
            "Exclude All Maps summaries when using per-map rows; do not add both/attack/defend together.",
            "Scoreboard FK/FD are not first-contact opportunities; clutch wins lack attempt denominators.",
            "Do not infer patch, lineup, personality or missing statistics from these records.",
            "Join stable provider IDs and historical roster dates before attaching video players.",
            "Split complete matches chronologically; fit normalizers only on training data.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--encoding", default="utf-8-sig")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.csv, args.encoding)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
