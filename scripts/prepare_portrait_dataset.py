"""Build a classifier dataset from independently reviewed, source-separated labels."""

import argparse
import csv
import hashlib
import json
import re
import shutil
from pathlib import Path


def prepare(review_csv, output):
    source = Path(review_csv).resolve()
    root = source.parent
    output = Path(output)
    if output.exists():
        raise ValueError("Output must be a new directory")
    with source.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    eligible = [
        row
        for row in rows
        if row.get("label_status") == "reviewed"
        and row.get("independent_review_status") == "reviewed"
        and row.get("reviewer_id")
    ]
    if not eligible:
        raise ValueError("No independently reviewed character labels")
    groups = {}
    planned = []
    for row in eligible:
        video, label, split = (
            row.get("video_id"),
            row.get("character_agent_id", ""),
            row.get("split"),
        )
        if (
            not video
            or split not in {"train", "val", "test"}
            or not re.fullmatch(r"[a-z][a-z0-9_]*", label)
        ):
            raise ValueError(
                "Each reviewed row needs video_id, character label and explicit train/val/test split"
            )
        if video in groups and groups[video] != split:
            raise ValueError("All images from one source video must remain in one split")
        groups[video] = split
        image = (root / row["image"]).resolve()
        if not image.is_relative_to(root) or not image.is_file():
            raise ValueError("Missing image or image outside dataset folder")
        planned.append((image, split, label))
    classes = {
        split: {label for _, partition, label in planned if partition == split}
        for split in ["train", "val"]
    }
    if len(classes["train"]) < 2 or classes["train"] != classes["val"]:
        raise ValueError("Train and validation must cover the same two or more character classes")
    seen_hashes = {}
    for image, split, _ in planned:
        digest = hashlib.sha256(image.read_bytes()).hexdigest()
        if digest in seen_hashes and seen_hashes[digest] != split:
            raise ValueError("Identical image bytes cross dataset splits")
        seen_hashes[digest] = split
    output.mkdir(parents=True)
    for image, split, label in planned:
        target = output / split / label
        target.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(str(image).encode()).hexdigest()[:12]
        shutil.copyfile(image, target / (digest + image.suffix))
    (output / "dataset_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "portrait_dataset_v1",
                "source_csv_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "source_splits": groups,
                "classes": sorted(classes["train"]),
                "images": len(planned),
                "note": "Source grouping does not independently guarantee match separation; check mirrored/edited uploads.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review_csv", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(prepare(args.review_csv, args.output))


if __name__ == "__main__":
    main()
