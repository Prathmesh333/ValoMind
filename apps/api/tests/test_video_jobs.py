import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "workers/analysis"))

from valomind_video.entities import resolve
from valomind_video.pipeline import Job, merge, video_id


def test_youtube_canonical_identity():
    assert video_id("https://youtu.be/omjZXmc7_4A?si=JbiLXLE-oCT4HFaC") == "omjZXmc7_4A"
    assert video_id("https://youtu.be/abcdefghijk?t=10") == "abcdefghijk"
    assert video_id("https://www.youtube.com/watch?v=abcdefghijk&list=ignored") == "abcdefghijk"
    with pytest.raises(ValueError):
        video_id("https://youtube.com.evil.example/watch?v=abcdefghijk")


def test_resume_empty_frames_and_deduplicate_exports(tmp_path):
    identity = {
        "video_id": "abcdefghijk",
        "source_url": "https://youtu.be/abcdefghijk",
        "source_sha256": "source",
        "model_sha256": "model",
    }
    job = Job(tmp_path, identity)
    job.commit(0, 0, [])
    job.commit(20, 1000, [{"kind": "ocr", "label": "text_region", "text": "Synthetic Blue"}])
    path = job.export()
    job.close()
    resumed = Job(tmp_path, identity)
    assert resumed.done(0) and resumed.done(20)
    resumed.close()
    output = merge([path, path], tmp_path / "merged.csv")
    with output.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    assert rows[0]["review_status"] == "proposed"
    assert rows[0]["player_id"] == ""


def test_different_model_creates_separate_job(tmp_path):
    a = Job(tmp_path, {"model": "a"})
    b = Job(tmp_path, {"model": "b"})
    assert a.id != b.id
    a.close()
    b.close()


def test_separate_entities_and_ambiguous_alias_abstention():
    catalog = [
        {"kind": "player", "id": "p1", "aliases": ["Alpha"]},
        {"kind": "team", "id": "t1", "aliases": ["Blue"]},
        {"kind": "map", "id": "m1", "aliases": ["Arena"]},
        {"kind": "character_agent", "id": "c1", "aliases": ["Scout"]},
    ]
    result = resolve(
        [
            {"kind": "ocr", "label": "text_region", "text": text}
            for text in ["ALPHA", "Blue", "Arena", "Scout"]
        ],
        catalog,
    )
    assert [row["kind"] for row in result] == [
        "entity.player",
        "entity.team",
        "entity.map",
        "entity.character_agent",
    ]
    assert "team_id" not in result[0]  # Seeing both names does not prove membership.
    catalog.append({"kind": "player", "id": "p2", "aliases": ["Alpha"]})
    assert resolve([{"kind": "ocr", "label": "text_region", "text": "Alpha"}], catalog) == []


def test_processing_loop_and_resume_with_fake_video(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from valomind_video import pipeline

    source = tmp_path / "source.mp4"
    source.write_bytes(b"synthetic fake decoder input")
    calls = []

    class Capture:
        def __init__(self, path):
            self.number = 0

        def get(self, prop):
            return 2.0

        def isOpened(self):
            return True

        def grab(self):
            self.number += 1
            return self.number <= 5

        def retrieve(self):
            return True, "fake_frame"

        def release(self):
            pass

    class Reader:
        def __init__(self, languages, gpu):
            pass

        def readtext(self, frame):
            calls.append(frame)
            return [([[0, 0], [10, 0], [10, 5], [0, 5]], "Alpha", 0.9)]

    monkeypatch.setitem(sys.modules, "cv2", SimpleNamespace(VideoCapture=Capture, CAP_PROP_FPS=5))
    monkeypatch.setitem(sys.modules, "easyocr", SimpleNamespace(Reader=Reader))
    monkeypatch.setattr(pipeline, "download", lambda url, root: source)
    monkeypatch.setattr("importlib.metadata.version", lambda name: "test")
    catalog = [{"kind": "player", "id": "p1", "aliases": ["Alpha"]}]
    args = {
        "url": "https://youtu.be/abcdefghijk",
        "root": tmp_path,
        "interval_seconds": 1.0,
        "catalog": catalog,
        "segment_filter": False,
        "review_sample_limit": 0,
    }
    output = pipeline.process(**args)
    assert len(calls) == 3
    assert pipeline.process(**args) == output
    assert len(calls) == 3  # Completed sampled frames are not inferred twice.
    with output.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 6
    assert {row["timestamp_ms"] for row in rows} == {"0", "1000", "2000"}
    assert {row["player_id"] for row in rows} == {"", "p1"}
    assert all(row["review_status"] == "proposed" for row in rows)
