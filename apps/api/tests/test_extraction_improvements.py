import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "workers/analysis"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_roster import CATALOG, ocr
from valomind_video.ocr_retry import retry_regions
from valomind_video.portraits import choose


def test_retry_targets_missing_field_without_lowering_name_threshold():
    rows = [ocr("Blue", 730, 10), ocr("Alpha", 80, 560)]
    regions = retry_regions(rows, 1920, 1080, CATALOG)
    assert regions == [("team", (1125, 0, 1200, 55))]


def test_retry_missing_slots_only_with_established_layout():
    catalog = {**CATALOG, "players": {"alpha": "p1", "beta": "p2", "gamma": "p3"}}
    rows = [ocr("Alpha", 80, 560), ocr("Beta", 80, 666), ocr("Gamma", 80, 772)]
    regions = retry_regions(rows, 1920, 1080, catalog)
    names = [box for kind, box in regions if kind == "player_name"]
    assert len(names) == 7
    assert (77, 550, 255, 595) not in names


def test_reference_margin_is_between_classes_not_two_same_agent_examples():
    result = choose([("a", 0.99), ("a", 0.98), ("b", 0.6)])
    assert result["character_agent_id"] == "a"
    assert result["status"] == "proposed"


@pytest.mark.parametrize("scores", [[("a", 0.7), ("b", 0.5)], [("a", 0.95), ("b", 0.94)]])
def test_unknown_for_weak_or_ambiguous_portraits(scores):
    assert choose(scores)["character_agent_id"] == ""


def test_constant_or_single_class_reference_does_not_force_identity():
    assert choose([])["character_agent_id"] == ""
    assert choose([("a", 1.0)])["status"] == "insufficient_reference_classes"


def test_crop_retry_translates_coordinates_and_keeps_originals(monkeypatch):
    from types import SimpleNamespace

    from valomind_video.ocr_retry import retry

    class Frame:
        shape = (1080, 1920, 3)

        def __getitem__(self, item):
            return "crop"

    class Reader:
        def readtext(self, image):
            return [([[3, 6], [33, 6], [33, 36], [3, 36]], "Red", 0.95)]

    monkeypatch.setitem(
        sys.modules, "cv2", SimpleNamespace(resize=lambda *a, **kw: "crop3x", INTER_CUBIC=2)
    )
    rows = [ocr("Blue", 730, 10), ocr("Alpha", 80, 560)]
    result = retry(Frame(), Reader(), rows, CATALOG)
    assert len(rows) == 2
    assert len(result) == 1
    assert result[0]["label"] == "retry.team"
    assert result[0]["x1"] == 1126
    assert result[0]["y1"] == 2


def test_learned_classifier_uses_single_device_and_abstains(monkeypatch, tmp_path):
    from types import SimpleNamespace

    from valomind_video.portraits import LearnedPortraitClassifier

    class Probabilities:
        def tolist(self):
            return [0.51, 0.49]

    class Model:
        task = "classify"

        def __init__(self):
            self.names = {0: "viper", 1: "fade"}

        def predict(self, image, device, verbose):
            assert device == "0"
            return [SimpleNamespace(probs=SimpleNamespace(data=Probabilities()))]

    monkeypatch.setitem(sys.modules, "ultralytics", SimpleNamespace(YOLO=lambda path: Model()))
    weights = tmp_path / "model.pt"
    weights.write_bytes(b"synthetic checkpoint double")
    classifier = LearnedPortraitClassifier(weights)
    assert classifier.predict("image")["status"] == "unknown"


def test_crop_retry_recovers_one_low_confidence_roster_name(monkeypatch):
    from types import SimpleNamespace

    from valomind_video.ocr_retry import retry
    from valomind_video.roster import parse_frame

    class Frame:
        shape = (1080, 1920, 3)

        def __getitem__(self, item):
            return "crop"

    class Reader:
        def readtext(self, image):
            return [([[30, 6], [120, 6], [120, 60], [30, 60]], "P8", 0.95)]

    catalog = {
        "players": {f"p{i}": f"p{i}" for i in range(1, 11)},
        "teams": {"blue": "t1", "red": "t2"},
        "maps": {},
    }
    rows = [ocr("Blue", 730, 10), ocr("Red", 1150, 10)]
    for i in range(1, 11):
        slot = (i - 1) % 5
        rows.append(
            ocr(
                f"P{i}",
                80 if i <= 5 else 1760,
                560 + 106 * slot,
                confidence=0.449 if i == 8 else 0.95,
            )
        )
    monkeypatch.setitem(
        sys.modules, "cv2", SimpleNamespace(resize=lambda *a, **kw: "crop3x", INTER_CUBIC=2)
    )
    assert len(parse_frame(rows, catalog=catalog)) == 9
    additional = retry(Frame(), Reader(), rows, catalog)
    additional = [
        {**rows[0], **row, "observation_id": f"retry:{i}"} for i, row in enumerate(additional)
    ]
    assert len(parse_frame([*rows, *additional], catalog=catalog)) == 10
