import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from prepare_portrait_dataset import prepare


def write_review(tmp_path, same_source=False, reviewed=True):
    rows = []
    for split in ["train", "val"]:
        for label in ["agent_a", "agent_b"]:
            image = f"{split}_{label}.jpg"
            (tmp_path / image).write_bytes(image.encode())
            rows.append(
                {
                    "image": image,
                    "video_id": "one" if same_source else split,
                    "character_agent_id": label,
                    "split": split,
                    "label_status": "reviewed" if reviewed else "proposed",
                    "independent_review_status": "reviewed" if reviewed else "pending",
                    "reviewer_id": "reviewer" if reviewed else "",
                }
            )
    path = tmp_path / "review.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_pending_labels_not_promoted_to_training(tmp_path):
    with pytest.raises(ValueError, match="No independently reviewed"):
        prepare(write_review(tmp_path, reviewed=False), tmp_path / "output")


def test_same_video_split_leakage_rejected(tmp_path):
    with pytest.raises(ValueError, match="one split"):
        prepare(write_review(tmp_path, same_source=True), tmp_path / "output")


def test_separate_sources_prepared_with_manifest(tmp_path):
    output = prepare(write_review(tmp_path), tmp_path / "output")
    assert (output / "dataset_manifest.json").is_file()
    assert len(list((output / "train/agent_a").glob("*.jpg"))) == 1
