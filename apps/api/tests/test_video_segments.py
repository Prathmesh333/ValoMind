import ast
import csv
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "workers/analysis"))

from valomind_video.pipeline import process
from valomind_video.segments import SegmentGate, classify, classify_probe


@pytest.mark.parametrize(
    ("texts", "expected"),
    [
        (["1:35", "6", "8"], "gameplay"),
        (["REPLAY", "1:35", "6", "8"], "replay"),
        (["BE RIGHT BACK"], "filler"),
        (["Analyst Desk"], "filler"),
        (["TEAM ROSTER"], "roster"),
        (["Some sponsor"], "uncertain"),
        (["1:35"], "uncertain"),
    ],
)
def test_hud_rules(texts, expected):
    assert classify(texts)[0] == expected


def test_transitions_do_not_leak_filler_or_replay():
    gate = SegmentGate(2)
    assert gate.update("gameplay") == ("uncertain", "review")
    assert gate.update("gameplay") == ("gameplay", "extract")
    assert gate.update("filler") == ("filler", "skip")
    assert gate.update("uncertain") == ("uncertain", "review")
    assert gate.update("replay") == ("replay", "skip")
    assert gate.update("roster") == ("uncertain", "review")
    state = dict(gate.state)
    resumed = SegmentGate(2)
    resumed.restore(state)
    assert resumed.update("roster") == ("roster", "extract")


def test_return_from_break_requires_confirmation_again():
    gate = SegmentGate(2)
    gate.update("gameplay")
    gate.update("gameplay")
    gate.update("filler")
    assert gate.update("gameplay") == ("uncertain", "review")
    assert gate.update("gameplay") == ("gameplay", "extract")


def test_broadcast_ocr_regression_missing_scores_and_period_timer():
    assert classify(["1.35", "0", "2"])[0] == "gameplay"
    actual_probe = [
        "CURRENT: SPLIT",
        "NEXT: SUMMIT",
        "NEXT: LOTUS",
        "RoUnD 1",
        "CHAMPIONS SHANGHAI | LOWER FINAL",
        "I0OT",
        "VIt",
        "1.35",
    ]
    assert classify(actual_probe)[0] == "gameplay"
    assert classify([*actual_probe, "REPLAY"])[0] == "replay"
    assert classify(["CURRENT: SPLIT", "NEXT: SUMMIT"])[0] == "uncertain"


def test_strong_same_frame_hud_admitted_without_waiting_for_another_sample():
    items = [
        {"text": "CURRENT: SPLIT", "confidence": 0.9, "x1": 20, "y1": 1, "x2": 150, "y2": 20},
        {"text": "NEXT: LOTUS", "confidence": 0.9, "x1": 240, "y1": 1, "x2": 350, "y2": 20},
        {"text": "1.35", "confidence": 0.9, "x1": 930, "y1": 20, "x2": 990, "y2": 60},
    ]
    candidate, _reason, strong = classify_probe(items, 1920, 1080)
    assert strong and candidate == "gameplay"
    gate = SegmentGate(2)
    assert gate.update(candidate, strong=strong) == ("gameplay", "extract")
    assert gate.update("uncertain") == ("uncertain", "review")
    assert gate.update("replay") == ("replay", "skip")
    items[-1].update(x1=1800, x2=1850)
    assert classify_probe(items, 1920, 1080)[2] is False


def test_replay_and_break_take_precedence_over_strong_hud():
    items = [
        {"text": text, "confidence": 0.9} for text in ["CURRENT: SPLIT", "NEXT: LOTUS", "1:35"]
    ]
    assert classify_probe([*items, {"text": "REPLAY", "confidence": 0.9}], 1920, 1080)[:1] == (
        "replay",
    )
    assert classify_probe([*items, {"text": "BE RIGHT BACK", "confidence": 0.9}], 1920, 1080)[
        :1
    ] == ("filler",)


def test_filter_skips_heavy_extraction_and_resumes(tmp_path, monkeypatch):
    source = tmp_path / "test.mp4"
    source.write_bytes(b"synthetic")
    signals = [
        ["1:35", "6", "8"],
        ["1:34", "6", "8"],
        ["BE RIGHT BACK"],
        ["Sponsor"],
        ["REPLAY"],
        ["TEAM ROSTER"],
        ["TEAM ROSTER"],
    ]
    full_calls = []
    probe_calls = []

    class Frame:
        shape = (100, 200, 3)

        def __init__(self, number):
            self.number = number

        def __getitem__(self, region):
            return self.number

    class Capture:
        def __init__(self, path):
            self.number = -1

        def isOpened(self):
            return True

        def get(self, prop):
            return 1.0

        def grab(self):
            self.number += 1
            return self.number < len(signals)

        def retrieve(self):
            return True, Frame(self.number)

        def release(self):
            pass

    class Reader:
        def __init__(self, languages, gpu):
            pass

        def readtext(self, frame):
            if isinstance(frame, int):
                probe_calls.append(frame)
                texts = signals[frame]
            else:
                full_calls.append(frame.number)
                texts = ["Alpha"]
            return [([[0, 0], [5, 0], [5, 5], [0, 5]], text, 0.9) for text in texts]

    monkeypatch.setitem(
        sys.modules,
        "cv2",
        SimpleNamespace(VideoCapture=Capture, CAP_PROP_FPS=5, imwrite=lambda path, frame: True),
    )
    monkeypatch.setitem(sys.modules, "easyocr", SimpleNamespace(Reader=Reader))
    monkeypatch.setattr("valomind_video.pipeline.download", lambda url, root: source)
    monkeypatch.setattr("importlib.metadata.version", lambda name: "test")
    args = {"url": "https://youtu.be/abcdefghijk", "root": tmp_path, "interval_seconds": 1.0}
    output = process(**args)
    assert full_calls == [1, 6]
    assert len(probe_calls) == 7
    assert process(**args) == output
    assert full_calls == [1, 6] and len(probe_calls) == 7
    with output.open(newline="", encoding="utf-8") as stream:
        observations = list(csv.DictReader(stream))
    assert [row["segment_type"] for row in observations] == ["gameplay", "roster"]
    with (output.parent / "segments.csv").open(newline="", encoding="utf-8") as stream:
        segments = list(csv.DictReader(stream))
    assert len(segments) == 7
    assert [row["processing_action"] for row in segments] == [
        "review",
        "extract",
        "skip",
        "review",
        "skip",
        "review",
        "extract",
    ]


def test_saved_broadcast_probe_regressions():
    root = Path(__file__).resolve().parents[3]
    examples = json.loads(
        (root / "packages/contracts/fixtures/hud_probe_regressions.json").read_text()
    )
    for example in examples:
        candidate, _, strong = classify_probe(example["items"], 1920, 1080)
        assert candidate == example["expected"]
        if candidate == "gameplay":
            assert strong


def test_notebook_code_cells_parse():
    root = Path(__file__).resolve().parents[3]
    notebook = json.loads((root / "notebooks/VCT_video_jobs.ipynb").read_text(encoding="utf-8"))
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            source = "".join(cell["source"])
            if source.startswith("%%writefile "):
                source = source.split("\n", 1)[1]
            ast.parse(source)
