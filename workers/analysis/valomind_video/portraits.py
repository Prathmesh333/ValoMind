"""Small reference-matching baseline with explicit abstention, not calibrated accuracy."""

import csv
import hashlib
import json
import math
from pathlib import Path

REFERENCE_VERSION = "portrait_reference_v1"


def choose(scores, min_score=0.80, min_margin=0.08):
    """Scores are feature cosine similarities, not probabilities."""
    if not 0 <= min_score <= 1 or not 0 <= min_margin <= 2:
        raise ValueError("Invalid reference thresholds")
    best = {}
    for label, score in scores:
        if not label or not math.isfinite(score):
            continue
        best[label] = max(best.get(label, -1), score)
    ranked = sorted(best.items(), key=lambda item: (-item[1], item[0]))
    if len(ranked) < 2:
        return {
            "character_agent_id": "",
            "score": None,
            "margin": None,
            "status": "insufficient_reference_classes",
        }
    (label, score), (_, runner_up) = ranked[:2]
    margin = score - runner_up
    accepted = score >= min_score and margin >= min_margin
    return {
        "character_agent_id": label if accepted else "",
        "score": score,
        "margin": margin,
        "status": "proposed" if accepted else "unknown",
    }


def feature(image):
    import cv2
    import numpy as np

    # Remove lower HUD border, preserve aspect ratio, and normalize contrast.
    gray = cv2.cvtColor(image[: max(1, round(image.shape[0] * 0.85))], cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    ratio = min(32 / width, 32 / height)
    gray = cv2.resize(gray, (max(1, round(width * ratio)), max(1, round(height * ratio))))
    canvas = np.zeros((32, 32), dtype=np.float32)
    y, x = (32 - gray.shape[0]) // 2, (32 - gray.shape[1]) // 2
    canvas[y : y + gray.shape[0], x : x + gray.shape[1]] = gray
    vector = canvas.ravel()
    vector -= vector.mean()
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm > 1e-6 else None


class PortraitMatcher:
    def __init__(self, reference_csv, allow_proposed=False, min_score=0.80, min_margin=0.08):
        import cv2

        self.min_score, self.min_margin = min_score, min_margin
        choose([], min_score, min_margin)
        path = Path(reference_csv).resolve()
        root = path.parent
        self.references = []
        digest = hashlib.sha256(path.read_bytes())
        with path.open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                reviewed = (
                    row.get("label_status") == "reviewed"
                    and row.get("independent_review_status") == "reviewed"
                    and bool(row.get("reviewer_id"))
                )
                if not reviewed and not (allow_proposed and row.get("label_status") == "proposed"):
                    continue
                if not row.get("character_agent_id"):
                    continue
                image_path = (root / row["image"]).resolve()
                if not image_path.is_relative_to(root):
                    raise ValueError("Reference image is outside its dataset folder")
                image = cv2.imread(str(image_path))
                if image is None:
                    raise ValueError(f"Unreadable reference image: {image_path.name}")
                vector = feature(image)
                if vector is not None:
                    self.references.append((row["character_agent_id"], vector))
                    digest.update(image_path.read_bytes())
        if len({label for label, _ in self.references}) < 2:
            raise ValueError(
                "Need at least two eligible reference classes; independent review is required by default"
            )
        self.identity = {
            "version": REFERENCE_VERSION,
            "sha256": digest.hexdigest(),
            "allow_proposed": allow_proposed,
            "min_score": min_score,
            "min_margin": min_margin,
            "method": "grayscale_cosine_reference",
        }

    def predict(self, image):
        vector = feature(image)
        scores = (
            []
            if vector is None
            else [(label, float(vector @ ref)) for label, ref in self.references]
        )
        return choose(scores, self.min_score, self.min_margin)


class LearnedPortraitClassifier:
    """Adapter for separately trained YOLO classification weights, with abstention."""

    def __init__(
        self, weights, device="0", min_score=0.80, min_margin=0.15, allowed_agent_ids=None
    ):
        from ultralytics import YOLO

        path = Path(weights)
        self.model = YOLO(str(path))
        if self.model.task != "classify":
            raise ValueError("Portrait weights must be an image classifier, not a HUD detector")
        allowed = set(allowed_agent_ids or ["chamber", "viper", "fade", "omen", "neon", "yoru"])
        allowed |= {"unknown", "other", "occluded"}
        if any(label not in allowed for label in self.model.names.values()):
            raise ValueError(
                "Classifier contains unapproved character classes; do not use generic ImageNet weights for extraction"
            )
        self.device = device
        self.min_score, self.min_margin = min_score, min_margin
        choose([], min_score, min_margin)
        self.identity = {
            "version": "portrait_classifier_v1",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "method": "yolo_classification",
            "min_score": min_score,
            "min_margin": min_margin,
            "allowed_classes": sorted(allowed),
        }

    def predict(self, image):
        result = self.model.predict(image, device=self.device, verbose=False)[0]
        values = result.probs.data.tolist()
        scores = [(self.model.names[i], float(value)) for i, value in enumerate(values)]
        output = choose(scores, self.min_score, self.min_margin)
        if output["character_agent_id"].casefold() in {"unknown", "other", "occluded"}:
            output.update(character_agent_id="", status="unknown")
        return output


def classify_rosters(roster_csv, matcher):
    import cv2

    path = Path(roster_csv)
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    # Keep roster output schema separate from optional portrait enrichment.
    fields = list(rows[0]) if rows else fields
    fields += ["portrait_status", "portrait_score", "portrait_margin", "portrait_model_version"]
    for row in rows:
        crop = path.parent / "portrait_proposals" / (row["roster_observation_id"] + ".jpg")
        image = cv2.imread(str(crop)) if crop.is_file() else None
        prediction = (
            matcher.predict(image)
            if image is not None
            else {"character_agent_id": "", "status": "missing_crop", "score": None, "margin": None}
        )
        row.update(
            character_agent_id=prediction["character_agent_id"],
            portrait_status=prediction["status"],
            portrait_score=prediction["score"],
            portrait_margin=prediction["margin"],
            portrait_model_version=matcher.identity["version"],
        )
    target = path.with_name("roster_with_agents.csv")
    if not fields:
        return None
    with target.with_suffix(".csv.tmp").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    target.with_suffix(".csv.tmp").replace(target)
    (path.parent / "portrait_model.json").write_text(
        json.dumps(matcher.identity, indent=2), encoding="utf-8"
    )
    return target
