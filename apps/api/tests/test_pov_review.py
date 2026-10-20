import sys
from pathlib import Path
from typing import ClassVar

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "workers/analysis"))

from valomind_video.pov import (
    EVENT_FIELDS,
    export_timings,
    propose_windows,
    read_table,
    write_table,
)


def evidence(tmp_path):
    rows = [
        {
            "frame_id": f"w:{i}",
            "window_id": "w",
            "source_sha256": "source",
            "timestamp_ms": timestamp,
        }
        for i, timestamp in enumerate([0, 10, 30, 65])
    ]
    frames = write_table(tmp_path / "frames.csv", rows, list(rows[0]))
    event = dict.fromkeys(EVENT_FIELDS, "") | {
        "event_id": "e",
        "window_id": "w",
        "player_id": "p",
        "cue_frame_id": "w:1",
        "action_frame_id": "w:3",
        "review_status": "reviewed",
        "reviewer_id": "analyst",
        "perspective": "player_pov",
        "cue_type": "enemy_first_visible",
        "action_type": "shot",
        "earlier_cues_unknown": "true",
        **dict.fromkeys(
            [
                "player_identity_verified",
                "xray_absent",
                "continuous_view",
                "cue_visibility_verified",
            ],
            "true",
        ),
    }
    return frames, event


def measure(tmp_path, event, frames):
    events = write_table(tmp_path / "events.csv", [event], EVENT_FIELDS)
    return read_table(export_timings(events, [frames], tmp_path / "response.csv"))[0]


def test_variable_frame_timing_uses_pts_and_brackets_uncertainty(tmp_path):
    frames, event = evidence(tmp_path)
    row = measure(tmp_path, event, frames)
    assert float(row["latency_ms"]) == 55
    assert float(row["latency_lower_ms"]) == 20
    assert float(row["latency_upper_ms"]) == 65
    assert row["metric"] == "visible_cue_to_action_latency"
    assert row["earlier_cues_unknown"] == "true"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("review_status", "proposed"),
        ("reviewer_id", ""),
        ("player_id", ""),
        ("perspective", "spectator"),
        ("xray_absent", "false"),
        ("continuous_view", "unknown"),
        ("cue_visibility_verified", "false"),
        ("player_identity_verified", "false"),
        ("cue_frame_id", "missing"),
        ("window_id", "other"),
        ("cue_frame_id", "w:0"),
        ("action_type", "thought"),
    ],
)
def test_unverified_or_mismatched_evidence_never_generates_numeric_latency(tmp_path, field, value):
    frames, event = evidence(tmp_path)
    event[field] = value
    row = measure(tmp_path, event, frames)
    assert row["latency_ms"] == ""
    assert row["exclusion_reason"]


def test_action_before_cue_is_excluded(tmp_path):
    frames, event = evidence(tmp_path)
    event.update(cue_frame_id="w:3", action_frame_id="w:1")
    assert measure(tmp_path, event, frames)["exclusion_reason"] == "action_precedes_cue"


def test_duplicate_frame_ids_are_rejected(tmp_path):
    frames, event = evidence(tmp_path)
    events = write_table(tmp_path / "events.csv", [event], EVENT_FIELDS)
    with pytest.raises(ValueError, match="Duplicate"):
        export_timings(events, [frames, frames], tmp_path / "response.csv")


def test_coverage_sampling_skips_fillers_and_limits_work(tmp_path):
    rows = [
        {
            "timestamp_ms": t * 1000,
            "segment_type": "gameplay" if t else "filler",
            "processing_action": "extract" if t else "skip",
        }
        for t in range(60)
    ]
    source = write_table(tmp_path / "segments.csv", rows, list(rows[0]))
    windows = propose_windows(source, limit=2)
    assert len(windows) == 2
    assert windows[0]["start_seconds"] >= 0
    assert windows[1]["start_seconds"] >= windows[0]["end_seconds"] + 10


def test_vit_exports_unlabeled_reviewed_crops_and_preserves_model_identity(tmp_path):
    Image = pytest.importorskip("PIL.Image")
    from valomind_video.visual_features import export_features

    Image.new("RGB", (20, 20), "red").save(tmp_path / "frame.png")
    row = {
        "sample_id": "s",
        "image_path": "frame.png",
        "x1": 0,
        "y1": 0,
        "x2": 10,
        "y2": 10,
        "crop_kind": "gameplay",
        "crop_review_status": "reviewed",
        "reviewer_id": "analyst",
        "source_sha256": "source",
        "timestamp_ms": 10,
    }
    samples = write_table(tmp_path / "samples.csv", [row], list(row))

    class FakeEncoder:
        identity: ClassVar = {"model_id": "synthetic-test-only", "revision": "fixture"}

        def __call__(self, images):
            return [[3, 4] for image in images]

    import json

    target = export_features(samples, tmp_path / "features.jsonl", FakeEncoder())
    result = json.loads(target.read_text())
    assert result["embedding"] == [0.6, 0.8]
    assert result["label_status"] == "unlabeled"
    assert result["model"] == FakeEncoder.identity
    row["crop_kind"] = "facecam"
    write_table(samples, [row], list(row))
    with pytest.raises(ValueError, match="Only reviewed"):
        export_features(samples, target, FakeEncoder())


def test_generated_notebook_cells_compile():
    import json

    root = Path(__file__).resolve().parents[3]
    notebook = json.loads((root / "notebooks/VCT_video_jobs.ipynb").read_text())
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), f"cell_{index}", "exec")
