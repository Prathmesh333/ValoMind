"""YouTube acquisition, sampled OCR/detection proposals, resumable CSV exports."""

import csv
import hashlib
import json
import math
import re
import sqlite3
from pathlib import Path
from urllib.parse import parse_qs, urlparse

VERSION = "video_v5"
FIELDS = [
    "observation_id",
    "job_id",
    "video_id",
    "source_url",
    "source_sha256",
    "model_sha256",
    "frame_index",
    "timestamp_ms",
    "kind",
    "label",
    "text",
    "confidence",
    "x1",
    "y1",
    "x2",
    "y2",
    "review_status",
    "player_id",
    "team_id",
    "map_id",
    "character_agent_id",
    "pipeline_version",
    "segment_type",
    "processing_action",
    "frame_width",
    "frame_height",
]


def channel_videos(
    url, limit=5, section="videos", cookie_file=None, js_runtime=None, export_root=None
):
    """List a bounded channel page without downloading media."""
    from yt_dlp import YoutubeDL
    from yt_dlp.utils import DownloadError

    from .acquisition import download_error_message, youtube_options

    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in {"youtube.com", "www.youtube.com"}
        or not re.fullmatch(r"/@[A-Za-z0-9_.-]+/?", parsed.path)
    ):
        raise ValueError("Expected an HTTPS YouTube @channel URL")
    if not 1 <= limit <= 50 or section not in {"videos", "streams"}:
        raise ValueError("Limit must be 1–50 and section videos or streams")
    target = f"https://www.youtube.com{parsed.path.rstrip('/')}/{section}"
    options = {
        "extract_flat": True,
        "playlistend": limit,
        "skip_download": True,
        **youtube_options(cookie_file, js_runtime, export_root),
    }
    try:
        with YoutubeDL(options) as ydl:
            listing = ydl.extract_info(target, download=False)
    except DownloadError as error:
        raise RuntimeError(download_error_message(error)) from None
    return [
        {
            "video_id": item["id"],
            "title": item.get("title", ""),
            "url": f"https://www.youtube.com/watch?v={item['id']}",
        }
        for item in listing.get("entries", [])
        if item and re.fullmatch(r"[A-Za-z0-9_-]{11}", item.get("id", ""))
    ][:limit]


def video_id(url):
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in {"youtube.com", "www.youtube.com", "youtu.be"}:
        raise ValueError("Use an HTTPS YouTube video link")
    value = (
        parsed.path.strip("/") if host == "youtu.be" else parse_qs(parsed.query).get("v", [""])[0]
    )
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        raise ValueError("Expected a single watch?v= or youtu.be video link")
    return value


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url, root, cookie_file=None, js_runtime=None):
    """Download a public video into the notebook runtime; do not bypass access restrictions."""
    from yt_dlp import YoutubeDL
    from yt_dlp.utils import DownloadError

    from .acquisition import cached_video, download_error_message, youtube_options

    key = video_id(url)
    folder = Path(root) / "sources" / key
    folder.mkdir(parents=True, exist_ok=True)
    existing = cached_video(folder, key)
    if existing:
        print("Reusing completed video from cloud cache; no YouTube request needed.")
        return existing
    options = {
        "noplaylist": True,
        "format": "bv*[height<=1080]+ba/b[height<=1080]",
        "merge_output_format": "mp4",
        "outtmpl": str(folder / "video.%(ext)s"),
        "writeinfojson": True,
        "continuedl": True,
        **youtube_options(cookie_file, js_runtime, root),
    }
    try:
        with YoutubeDL(options) as downloader:
            info = downloader.extract_info(f"https://www.youtube.com/watch?v={key}", download=True)
            requested = info.get("requested_downloads") or []
            candidates = [Path(info.get("filepath") or downloader.prepare_filename(info))]
            candidates += [Path(item["filepath"]) for item in requested if item.get("filepath")]
            candidates = [
                folder / "video.mp4",
                *candidates,
                folder / "video.webm",
                folder / "video.mkv",
            ]
            for candidate in candidates:
                if candidate.is_file() and not re.search(r"\.f\d+\.", candidate.name):
                    return candidate
    except DownloadError as error:
        raise RuntimeError(download_error_message(error)) from None
    raise RuntimeError("Download completed without a readable merged video")


def write_csv(path, rows):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(target)


class Job:
    """One SQLite file per job. Commit each sampled frame, including empty frames."""

    def __init__(self, root, identity):
        self.identity = identity
        self.id = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:24]
        self.folder = Path(root) / "jobs" / self.id
        self.folder.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.folder / "state.sqlite")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS frames (number INTEGER PRIMARY KEY, rows TEXT NOT NULL)"
        )
        (self.folder / "manifest.json").write_text(json.dumps(identity, indent=2), encoding="utf-8")

    def done(self, number):
        return (
            self.db.execute("SELECT 1 FROM frames WHERE number=?", (number,)).fetchone() is not None
        )

    def restore_gate(self, number, gate):
        encoded = self.db.execute("SELECT rows FROM frames WHERE number=?", (number,)).fetchone()[0]
        for row in json.loads(encoded):
            if row["kind"] == "segment":
                gate.restore(json.loads(row["text"])["gate_state"])

    def records(self, number, timestamp_ms, proposals):
        rows = []
        for i, proposal in enumerate(proposals):
            row = dict.fromkeys(FIELDS, "")
            row.update(proposal)
            row.update(
                observation_id=f"{self.id}:{number}:{i}",
                job_id=self.id,
                video_id=self.identity["video_id"],
                source_url=self.identity["source_url"],
                source_sha256=self.identity["source_sha256"],
                model_sha256=self.identity["model_sha256"],
                frame_index=number,
                timestamp_ms=timestamp_ms,
                review_status="proposed",
                pipeline_version=VERSION,
            )
            rows.append(row)
        return rows

    def commit(self, number, timestamp_ms, proposals):
        rows = self.records(number, timestamp_ms, proposals)
        with self.db:
            self.db.execute("INSERT INTO frames VALUES (?, ?)", (number, json.dumps(rows)))

    def export(self):
        def rows(segment=False):
            for (encoded,) in self.db.execute("SELECT rows FROM frames ORDER BY number"):
                yield from (
                    row for row in json.loads(encoded) if (row["kind"] == "segment") == segment
                )

        path = self.folder / "observations.csv"
        write_csv(path, rows())
        write_csv(self.folder / "segments.csv", rows(segment=True))
        from .segments import export_review_queue

        export_review_queue(self.folder / "segments.csv")
        from .roster import export_rosters

        export_rosters(path, catalog=self.identity.get("roster_catalog"))
        if getattr(self, "portrait_matcher", None) is not None:
            from .portraits import classify_rosters

            classify_rosters(path.with_name("roster_observations.csv"), self.portrait_matcher)
        return path

    def close(self):
        self.db.close()


def process(
    url,
    root,
    weights=None,
    interval_seconds=2.0,
    device="cpu",
    end_seconds=None,
    catalog=None,
    segment_filter=True,
    confirm_samples=2,
    save_portrait_crops=True,
    roster_catalog=None,
    crop_ocr_retry=True,
    portrait_reference_csv=None,
    portrait_classifier_weights=None,
    portrait_allowed_classes=None,
    allow_proposed_portrait_references=False,
    review_sample_limit=24,
    cookie_file=None,
    js_runtime=None,
):
    """OCR bootstrap works without weights; optional YOLO adds custom detector proposals."""
    import cv2
    import easyocr

    from .entities import resolve, validate_catalog
    from .ocr_retry import RETRY_VERSION, retry
    from .roster import PROFILE_VERSION, SOURCE_CATALOG, parse_frame
    from .segments import RULE_VERSION, SegmentGate, classify_probe

    catalog = validate_catalog(catalog or [])
    gate = SegmentGate(confirm_samples)
    if not isinstance(review_sample_limit, int) or review_sample_limit < 0:
        raise ValueError("review_sample_limit must be a nonnegative integer")
    portrait_matcher = None
    if portrait_reference_csv and portrait_classifier_weights:
        raise ValueError("Choose reference matching or learned classification, not both")
    if portrait_classifier_weights:
        from .portraits import LearnedPortraitClassifier

        if not save_portrait_crops:
            raise ValueError("Portrait classification requires saved portrait crops")
        portrait_matcher = LearnedPortraitClassifier(
            portrait_classifier_weights, device=device, allowed_agent_ids=portrait_allowed_classes
        )
    if portrait_reference_csv:
        from .portraits import PortraitMatcher

        if not save_portrait_crops:
            raise ValueError("Portrait classification requires saved portrait crops")
        portrait_matcher = PortraitMatcher(
            portrait_reference_csv, allow_proposed=allow_proposed_portrait_references
        )

    if not math.isfinite(interval_seconds) or interval_seconds <= 0:
        raise ValueError("Sampling interval must be finite and positive")
    if end_seconds is not None and (not math.isfinite(end_seconds) or end_seconds <= 0):
        raise ValueError("End time must be finite and positive")
    model = None
    model_hash = "none-ocr-bootstrap"
    if weights:
        from ultralytics import YOLO

        model_hash = sha256(weights)
        model = YOLO(str(weights))
        if model.task != "detect":
            raise ValueError("Expected object detection weights")
    source = (
        download(url, root, cookie_file=cookie_file, js_runtime=js_runtime)
        if cookie_file or js_runtime
        else download(url, root)
    )
    key = video_id(url)
    roster_catalog = roster_catalog or SOURCE_CATALOG.get(key)
    import importlib.metadata

    versions = {
        name: importlib.metadata.version(name) for name in ["easyocr", "opencv-python-headless"]
    }
    if model:
        versions["ultralytics"] = importlib.metadata.version("ultralytics")
    job = Job(
        root,
        {
            "pipeline_version": VERSION,
            "video_id": key,
            "source_url": f"https://www.youtube.com/watch?v={key}",
            "source_sha256": sha256(source),
            "model_sha256": model_hash,
            "interval_seconds": interval_seconds,
            "end_seconds": end_seconds,
            "device": device,
            "packages": versions,
            "source_rights_status": "unconfirmed",
            "is_synthetic": False,
            "catalog": catalog,
            "segment_filter": segment_filter,
            "segment_rule_version": RULE_VERSION,
            "confirm_samples": confirm_samples,
            "roster_profile_version": PROFILE_VERSION,
            "save_portrait_crops": save_portrait_crops,
            "roster_catalog": roster_catalog,
            "crop_ocr_retry": crop_ocr_retry,
            "retry_version": RETRY_VERSION,
            "portrait_matcher": portrait_matcher.identity if portrait_matcher else None,
            "review_sample_limit": review_sample_limit,
        },
    )
    job.portrait_matcher = portrait_matcher
    review_folder = job.folder / "segment_review"
    review_count = len(list(review_folder.glob("*.jpg")))
    cap = cv2.VideoCapture(str(source))
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        if not cap.isOpened() or not math.isfinite(fps) or fps <= 0:
            raise ValueError("Cannot decode video or determine frame rate")
        step = max(1, round(fps * interval_seconds))
        ocr_device = False if device == "cpu" else f"cuda:{device}"
        reader = easyocr.Reader(["en"], gpu=ocr_device)
        number = 0
        processed = 0
        while end_seconds is None or number / fps < end_seconds:
            if not cap.grab():
                break
            if number % step == 0 and job.done(number):
                job.restore_gate(number, gate)
            elif number % step == 0:
                ok, frame = cap.retrieve()
                if not ok:
                    raise RuntimeError(f"Frame decode failed at {number}")
                proposals = []
                segment_type, action, reason = "unfiltered", "extract", "Filter disabled"
                probe = []
                probe_items = []
                if segment_filter:
                    height = frame.shape[0]
                    probe = reader.readtext(frame[: max(1, round(height * 0.24)), :])
                    for box, text, confidence in probe:
                        xs, ys = zip(*box, strict=True)
                        probe_items.append(
                            {
                                "text": text,
                                "confidence": float(confidence),
                                "x1": float(min(xs)),
                                "y1": float(min(ys)),
                                "x2": float(max(xs)),
                                "y2": float(max(ys)),
                            }
                        )
                    candidate, reason, strong = classify_probe(probe_items, frame.shape[1], height)
                    segment_type, action = gate.update(candidate, strong=strong)
                proposals.append(
                    {
                        "kind": "segment",
                        "label": segment_type,
                        "segment_type": segment_type,
                        "processing_action": action,
                        "text": json.dumps(
                            {
                                "reason": reason,
                                "gate_state": gate.state,
                                "probe_text": [text for _, text, _ in probe],
                                "probe_items": probe_items,
                            }
                        ),
                    }
                )
                readings = reader.readtext(frame) if action == "extract" else []
                for box, text, confidence in readings:
                    xs, ys = zip(*box, strict=True)
                    proposals.append(
                        {
                            "kind": "ocr",
                            "label": "text_region",
                            "text": text,
                            "confidence": float(confidence),
                            "x1": float(min(xs)),
                            "y1": float(min(ys)),
                            "x2": float(max(xs)),
                            "y2": float(max(ys)),
                        }
                    )
                if model and action == "extract":
                    result = model.predict(frame, device=device, verbose=False, conf=0.25)[0]
                    for box in result.boxes:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        proposals.append(
                            {
                                "kind": "detection",
                                "label": result.names[int(box.cls.item())],
                                "confidence": float(box.conf.item()),
                                "x1": x1,
                                "y1": y1,
                                "x2": x2,
                                "y2": y2,
                            }
                        )
                if crop_ocr_retry and action == "extract" and roster_catalog is not None:
                    shape = frame.shape
                    records = job.records(number, round(number / fps * 1000), proposals)
                    proposals.extend(retry(frame, reader, records, catalog=roster_catalog))
                if number // step % 5 == 0 and review_count < review_sample_limit:
                    review_folder.mkdir(exist_ok=True)
                    review_image = review_folder / f"{number:09d}.jpg"
                    if not cv2.imwrite(str(review_image), frame):
                        raise RuntimeError("Could not save segment review frame")
                    review_count += 1
                    details = json.loads(proposals[0]["text"])
                    details["review_image"] = f"segment_review/{review_image.name}"
                    proposals[0]["text"] = json.dumps(details)
                proposals.extend(resolve(proposals, catalog))
                for proposal in proposals:
                    proposal.update(segment_type=segment_type, processing_action=action)
                    shape = getattr(frame, "shape", (1080, 1920))
                    proposal.update(frame_width=shape[1], frame_height=shape[0])
                if save_portrait_crops and action == "extract":
                    # Save crops before committing the frame, so failed writes can retry.
                    records = job.records(number, round(number / fps * 1000), proposals)
                    for roster in parse_frame(
                        records, width=shape[1], height=shape[0], catalog=roster_catalog
                    ):
                        crop = frame[
                            roster["portrait_y1"] : roster["portrait_y2"],
                            roster["portrait_x1"] : roster["portrait_x2"],
                        ]
                        folder = job.folder / "portrait_proposals"
                        folder.mkdir(exist_ok=True)
                        if not cv2.imwrite(
                            str(folder / f"{roster['roster_observation_id']}.jpg"), crop
                        ):
                            raise RuntimeError("Could not save portrait proposal")
                job.commit(number, round(number / fps * 1000), proposals)
                processed += 1
                if processed % 25 == 0:
                    job.export()
                    print(
                        f"Saved {processed} additional sampled frames; source time {number / fps:.1f}s"
                    )
            number += 1
        if number == 0:
            raise RuntimeError("Video decoded no frames")
        return job.export()
    finally:
        cap.release()
        job.export()
        job.close()


def merge(inputs, output):
    """Deduplicate identical jobs; retain different model versions and reject collisions."""
    rows = {}
    for path in inputs:
        with Path(path).open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != FIELDS:
                raise ValueError(f"Incompatible CSV schema: {path}")
            for row in reader:
                key = row["observation_id"]
                if not key:
                    raise ValueError("Missing observation ID")
                if key in rows and rows[key] != row:
                    raise ValueError(f"Conflicting observation: {key}")
                rows[key] = row
    write_csv(output, (rows[key] for key in sorted(rows)))
    return Path(output)
