"""Stage scene-label proposals for review; never manufacture train/validation splits."""

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path


def read(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def prepare(annotation_dir, output, interval_ms=250, min_duration_ms=500, margin_ms=100):
    annotation_dir, output = Path(annotation_dir).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("Use a new output directory; existing review data is never overwritten")
    if interval_ms < 100 or min_duration_ms < 500 or margin_ms < 0:
        raise ValueError("Use interval >=100ms, minimum duration >=500ms and nonnegative margin")
    scenes = read(annotation_dir / "scene_segments_proposed.csv")
    frames = read(annotation_dir / "frame_labels_proposed.csv")
    grouped = {}
    ids = set()
    for frame in frames:
        if frame["frame_id"] in ids:
            raise ValueError("Duplicate frame ID")
        ids.add(frame["frame_id"])
        grouped.setdefault(frame["segment_id"], []).append(frame)
    planned, excluded, seen_images = [], [], {}
    for scene in scenes:
        begin, end = float(scene["start_ms"]), float(scene["end_ms_inclusive"])
        reason = ""
        if scene["scene_label"] == "transition_uncertain" or scene["perspective"] == "unknown":
            reason = "uncertain_transition"
        elif end - begin < min_duration_ms:
            reason = "shorter_than_minimum_stable_duration"
        if reason:
            excluded.append({"segment_id": scene["segment_id"], "reason": reason})
            continue
        next_sample = begin + margin_ms
        for frame in sorted(
            grouped.get(scene["segment_id"], []), key=lambda row: float(row["timestamp_ms"])
        ):
            timestamp = float(frame["timestamp_ms"])
            if not begin <= timestamp <= end:
                raise ValueError("Frame falls outside its scene interval")
            if timestamp < next_sample or timestamp > end - margin_ms:
                continue
            if (
                frame["scene_label"] != scene["scene_label"]
                or frame["perspective"] != scene["perspective"]
                or frame["window_id"] != scene["window_id"]
            ):
                raise ValueError("Frame/scene label mismatch")
            image = (annotation_dir / frame["image_path"]).resolve()
            # References may leave annotation_dir, but must stay in the private results workspace.
            if not image.is_relative_to(annotation_dir.parent) or not image.is_file():
                raise ValueError("Missing image or image outside the review workspace")
            checksum = hashlib.sha256(image.read_bytes()).hexdigest()
            targets = (scene["scene_label"], scene["perspective"])
            if checksum in seen_images:
                if seen_images[checksum] != targets:
                    raise ValueError("Identical image has conflicting proposal labels")
                continue
            seen_images[checksum] = targets
            next_sample = timestamp + interval_ms
            name = hashlib.sha256(frame["frame_id"].encode()).hexdigest()[:24] + ".jpg"
            planned.append(
                (
                    image,
                    {
                        "sample_id": frame["frame_id"],
                        "image": "images/" + name,
                        "image_sha256": checksum,
                        "source_sha256": scene["source_sha256"],
                        "window_id": scene["window_id"],
                        "segment_id": scene["segment_id"],
                        "timestamp_ms": frame["timestamp_ms"],
                        "scene_label": scene["scene_label"],
                        "perspective": scene["perspective"],
                        "label_status": "proposed",
                        "annotator": "assistant_vision",
                        "independent_review_status": "pending",
                        "reviewer_id": "",
                        "split": "unassigned",
                        "training_eligible": "false",
                    },
                )
            )
    if not planned:
        raise ValueError("No eligible stable proposal samples")
    output.mkdir(parents=True)
    (output / "images").mkdir()
    for source, row in planned:
        shutil.copyfile(source, output / row["image"])
    with (output / "samples_proposed.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(planned[0][1]))
        writer.writeheader()
        writer.writerows(row for _, row in planned)
    sources = {row["source_sha256"] for _, row in planned}
    report = {
        "schema_version": "scene_proposal_dataset_v1",
        "samples": len(planned),
        "source_groups": len(sources),
        "source_group_ids": sorted(sources),
        "scene_counts": dict(Counter(row["scene_label"] for _, row in planned)),
        "perspective_counts": dict(Counter(row["perspective"] for _, row in planned)),
        "excluded_segments": excluded,
        "sampling_interval_ms": interval_ms,
        "boundary_margin_ms": margin_ms,
        "minimum_stable_duration_ms": min_duration_ms,
        "training_ready": False,
        "independently_reviewed_samples": 0,
        "validation_split_created": False,
        "test_split_created": False,
        "blocking_requirements": [
            "Independent label review with provenance",
            "Additional source matches for grouped evaluation",
        ],
        "notes": "Scene and perspective are separate targets. Same-source windows remain one group. No player traits or reaction-time labels.",
    }
    (output / "dataset_manifest.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("annotation_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.annotation_dir, args.output), indent=2))
