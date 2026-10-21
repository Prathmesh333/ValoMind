import ast
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "workers/analysis"))

from valomind_video.batch import OFFICIAL_CHANNEL, run_queue, validate_sources
from valomind_video.pipeline import process


def sources():
    return [
        {
            "video_id": "abcdefghijk",
            "url": "https://youtu.be/abcdefghijk",
            "title": "Synthetic archived playoff fixture",
            "channel_id": OFFICIAL_CHANNEL,
            "duration_seconds": 18000,
            "is_live_now": False,
            "is_live_content": True,
            "dataset_role": "train_proposed",
        }
    ]


def test_queue_resumes_same_worker_output_and_skips_complete(tmp_path):
    calls = []

    def worker(source):
        calls.append(source["video_id"])
        output = tmp_path / "observations.csv"
        output.write_text("synthetic fixture")
        return {"output_csv": output, "complete": len(calls) == 2}

    state = run_queue(sources(), tmp_path, worker, {"recipe": "test"})
    assert state["jobs"]["abcdefghijk"]["status"] == "complete"
    assert len(calls) == 2
    run_queue(sources(), tmp_path, worker, {"recipe": "test"})
    assert len(calls) == 2
    with pytest.raises(ValueError, match="configuration changed"):
        run_queue(sources(), tmp_path, worker, {"recipe": "changed"})


def test_bot_block_stops_and_never_retries_without_configuration(tmp_path):
    calls = []

    def worker(source):
        calls.append(source)
        raise RuntimeError("YouTube requires sign-in verification")

    state = run_queue(sources(), tmp_path, worker, {})
    assert state["jobs"]["abcdefghijk"]["status"] == "blocked"
    run_queue(sources(), tmp_path, worker, {})
    assert len(calls) == 1


@pytest.mark.parametrize(
    "change",
    [
        {"channel_id": "other"},
        {"is_live_now": True},
        {"duration_seconds": 120},
        {"dataset_role": "random_frames"},
    ],
)
def test_source_catalog_rejects_wrong_owner_live_short_or_wrong_split(change):
    with pytest.raises(ValueError):
        validate_sources([sources()[0] | change])


def test_seek_sampling_checkpoints_without_decoding_completed_frames(tmp_path, monkeypatch):
    source = tmp_path / "video.mp4"
    source.write_bytes(b"synthetic media fixture")
    grabs = []

    class Frame:
        shape = (1080, 1920, 3)

    class Capture:
        def __init__(self, path):
            self.number = 0

        def isOpened(self):
            return True

        def get(self, prop):
            return {1: 2, 2: 20, 3: self.number + 1}[prop]

        def set(self, prop, number):
            self.number = number
            return True

        def grab(self):
            grabs.append(self.number)
            return True

        def retrieve(self):
            return True, Frame()

        def release(self):
            pass

    class Reader:
        def __init__(self, languages, gpu):
            assert gpu == "cuda:0"

        def readtext(self, frame):
            return []

    monkeypatch.setitem(
        sys.modules,
        "cv2",
        SimpleNamespace(
            VideoCapture=Capture, CAP_PROP_FPS=1, CAP_PROP_FRAME_COUNT=2, CAP_PROP_POS_FRAMES=3
        ),
    )
    monkeypatch.setitem(sys.modules, "easyocr", SimpleNamespace(Reader=Reader))
    monkeypatch.setattr("valomind_video.pipeline.download", lambda url, root: source)
    monkeypatch.setattr("importlib.metadata.version", lambda name: "fixture")
    args = {
        "url": "https://youtu.be/abcdefghijk",
        "root": tmp_path,
        "sampling_mode": "seek",
        "interval_seconds": 1,
        "device": "0",
        "segment_filter": False,
        "save_portrait_crops": False,
        "crop_ocr_retry": False,
        "review_sample_limit": 0,
    }
    first = process(**args, max_new_samples=3)
    assert grabs == [0, 2, 4]
    assert not json.loads((first.parent / "progress.json").read_text())["complete"]
    assert process(**args, max_new_samples=3) == first
    assert grabs == [0, 2, 4, 6, 8, 10]
    assert process(**args) == first
    assert grabs == list(range(0, 20, 2))
    assert json.loads((first.parent / "progress.json").read_text())["complete"]
    process(**args)
    assert grabs == list(range(0, 20, 2))


def test_prefilled_batch_has_five_official_unique_archives_and_parseable_cells():
    root = Path(__file__).resolve().parents[3]
    catalog = json.loads((root / "configs/vct_playoffs_sources.json").read_text())["sources"]
    assert len(validate_sources(catalog)) == 5
    assert len({row["video_id"] for row in catalog}) == 5
    assert sum(row["dataset_role"] == "test_reserved" for row in catalog) == 1
    notebook = json.loads((root / "notebooks/VCT_playoffs_batch.ipynb").read_text(encoding="utf-8"))
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] == "code":
            ast.parse("".join(cell["source"]), filename=f"batch_cell_{index}")
