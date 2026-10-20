"""Optional frozen ViT features for reviewed gameplay crops, never facial profiling."""

import hashlib
import json
import math
import re
from pathlib import Path

from .pov import read_table, write_table

VERSION = "visual_features_v1"


class DinoEncoder:
    """Small frozen DINOv2 on a single CUDA GPU; no automatic label generation."""

    def __init__(self, revision, device="cuda:0"):
        import torch
        from transformers import AutoImageProcessor, AutoModel

        if not re.fullmatch(r"[a-f0-9]{40}", revision):
            raise ValueError("Pin an immutable Hugging Face model commit SHA")
        if device != "cuda:0" or not torch.cuda.is_available():
            raise ValueError("This optional encoder requires the single CUDA GPU at cuda:0")
        self.torch = torch
        self.device = device
        self.processor = AutoImageProcessor.from_pretrained(
            "facebook/dinov2-small", revision=revision
        )
        self.model = (
            AutoModel.from_pretrained(
                "facebook/dinov2-small", revision=revision, use_safetensors=True
            )
            .eval()
            .to(device)
        )
        self.identity = {
            "model_id": "facebook/dinov2-small",
            "revision": revision,
            "device": device,
            "precision": "float16_autocast",
        }

    def __call__(self, images):
        torch = self.torch
        inputs = self.processor(images=images, return_tensors="pt").to(self.device)
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.float16):
            features = self.model(**inputs).last_hidden_state[:, 0].float()
            features = torch.nn.functional.normalize(features, dim=-1)
        return features.cpu().tolist()


def export_features(samples_csv, destination, encoder, batch_size=4):
    """Explicit reviewed crop bounds prevent embedding whole broadcasts/facecams.

    Coordinates are pixels in the saved image. Embeddings remain unlabeled.
    Caller supplies an encoder so tests require neither CUDA nor model downloads.
    """
    from PIL import Image

    if not 1 <= batch_size <= 16:
        raise ValueError("Use batch size 1–16 on a single GPU")
    samples = read_table(samples_csv)
    if not 1 <= len(samples) <= 2000:
        raise ValueError("Select 1–2000 reviewed crops")
    ids = set()
    for row in samples:
        if not row["sample_id"] or row["sample_id"] in ids:
            raise ValueError("Sample IDs must be unique and nonempty")
        ids.add(row["sample_id"])
        if row["crop_review_status"] != "reviewed" or row["crop_kind"] not in {
            "gameplay",
            "character_portrait",
        }:
            raise ValueError("Only reviewed gameplay or character portrait crops are allowed")
        if not row["reviewer_id"] or not row["source_sha256"] or not row["timestamp_ms"]:
            raise ValueError("Crop reviewer and source/time provenance are required")
    rows, dimensions = [], None
    for offset in range(0, len(samples), batch_size):
        batch = samples[offset : offset + batch_size]
        images, hashes = [], []
        for row in batch:
            path = Path(row["image_path"])
            if not path.is_absolute():
                path = Path(samples_csv).parent / path
            with Image.open(path) as source:
                box = tuple(int(row[key]) for key in ["x1", "y1", "x2", "y2"])
                if (
                    not 0 <= box[0] < box[2] <= source.width
                    or not 0 <= box[1] < box[3] <= source.height
                ):
                    raise ValueError("Crop coordinates fall outside the saved image")
                crop = source.convert("RGB").crop(box)
                images.append(crop)
                hashes.append(hashlib.sha256(crop.tobytes()).hexdigest())
        vectors = encoder(images)
        if len(vectors) != len(batch):
            raise ValueError("Encoder returned an incorrect batch size")
        for row, vector, crop_hash in zip(batch, vectors, hashes, strict=True):
            vector = [float(value) for value in vector]
            norm = math.sqrt(sum(value * value for value in vector))
            if not vector or not math.isfinite(norm) or norm == 0:
                raise ValueError("Encoder returned an invalid vector")
            dimensions = dimensions or len(vector)
            if len(vector) != dimensions:
                raise ValueError("Embedding dimensions changed")
            rows.append(
                dict(
                    row,
                    embedding=[value / norm for value in vector],
                    crop_sha256=crop_hash,
                    model=encoder.identity,
                    label_status="unlabeled",
                    schema_version=VERSION,
                )
            )
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    temporary.replace(destination)
    # Farthest-first review selection is diversity, not uncertainty or confidence.
    chosen, remaining = [], list(range(len(rows)))
    distances = [2.0] * len(rows)
    while remaining and len(chosen) < 100:
        index = max(remaining, key=lambda candidate: distances[candidate])
        chosen.append(index)
        remaining.remove(index)
        for other in remaining:
            distance = 1 - sum(
                a * b
                for a, b in zip(rows[index]["embedding"], rows[other]["embedding"], strict=True)
            )
            distances[other] = min(distances[other], distance)
    queue = [
        {
            "sample_id": rows[index]["sample_id"],
            "diversity_rank": rank + 1,
            "label": "",
            "review_status": "unreviewed",
        }
        for rank, index in enumerate(chosen)
    ]
    write_table(destination.with_suffix(".review_queue.csv"), queue, list(queue[0]))
    return destination
