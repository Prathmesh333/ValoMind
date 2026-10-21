import csv
import importlib.util
from pathlib import Path

import pytest


def module():
    path = Path(__file__).resolve().parents[3] / "scripts/prepare_scene_proposals.py"
    spec = importlib.util.spec_from_file_location("scene_proposals", path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def table(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def fixtures(tmp_path):
    annotations = tmp_path / "annotations"
    annotations.mkdir()
    scenes = [
        {
            "segment_id": "s",
            "window_id": "w",
            "start_ms": "0",
            "end_ms_inclusive": "1000",
            "scene_label": "buy_phase",
            "perspective": "observer",
            "source_sha256": "synthetic-source",
        }
    ]
    frames = []
    for index in range(11):
        # Byte fixtures only: these tests exercise provenance/sampling, not image decoding.
        image = annotations / f"fixture_{index}.jpg"
        image.write_bytes(f"synthetic image bytes {index}".encode())
        frames.append(
            {
                "frame_id": f"w:{index}",
                "segment_id": "s",
                "window_id": "w",
                "timestamp_ms": str(index * 100),
                "scene_label": "buy_phase",
                "perspective": "observer",
                "image_path": image.name,
            }
        )
    table(annotations / "scene_segments_proposed.csv", scenes)
    table(annotations / "frame_labels_proposed.csv", frames)
    return annotations, scenes, frames


def test_proposals_never_become_reviewed_or_randomly_split(tmp_path):
    annotations, _, _ = fixtures(tmp_path)
    output = tmp_path / "dataset"
    report = module().prepare(annotations, output)
    assert report["samples"] == 3
    assert report["source_groups"] == 1
    assert not report["training_ready"]
    assert not report["validation_split_created"]
    rows = module().read(output / "samples_proposed.csv")
    assert [int(row["timestamp_ms"]) for row in rows] == [100, 400, 700]
    assert all(row["label_status"] == "proposed" and row["split"] == "unassigned" for row in rows)
    assert all(row["training_eligible"] == "false" and not row["reviewer_id"] for row in rows)
    with pytest.raises(ValueError, match="new output"):
        module().prepare(annotations, output)


def test_cross_window_assignment_is_rejected(tmp_path):
    annotations, _, frames = fixtures(tmp_path)
    frames[1]["window_id"] = "other-window"
    table(annotations / "frame_labels_proposed.csv", frames)
    with pytest.raises(ValueError, match="label mismatch"):
        module().prepare(annotations, tmp_path / "dataset")


def test_unknown_transition_is_excluded(tmp_path):
    annotations, scenes, frames = fixtures(tmp_path)
    scenes[0]["scene_label"] = "transition_uncertain"
    for row in frames:
        row["scene_label"] = "transition_uncertain"
    table(annotations / "scene_segments_proposed.csv", scenes)
    table(annotations / "frame_labels_proposed.csv", frames)
    with pytest.raises(ValueError, match="No eligible stable"):
        module().prepare(annotations, tmp_path / "dataset")
