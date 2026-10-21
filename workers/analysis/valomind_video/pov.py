"""Offline POV review windows and evidence-gated cue-to-action measurements.

No action detector or psychological inference is implied by these exports.
"""

import csv
import hashlib
import json
import math
import shutil
from pathlib import Path

VERSION = "pov_review_v1"
EVENT_FIELDS = [
    "event_id",
    "window_id",
    "player_id",
    "team_id",
    "map_id",
    "round_id",
    "cue_type",
    "action_type",
    "cue_frame_id",
    "action_frame_id",
    "review_status",
    "reviewer_id",
    "perspective",
    "player_identity_verified",
    "xray_absent",
    "continuous_view",
    "cue_visibility_verified",
    "earlier_cues_unknown",
    "notes",
]


def write_table(path, rows, fields):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)
    return path


def read_table(path):
    with Path(path).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def propose_windows(segments_csv, limit=6, seconds=4.0):
    """Bounded coverage samples, not detected events or confirmed player POVs."""
    if not 1 <= limit <= 20 or not math.isfinite(seconds) or not 0 < seconds <= 8:
        raise ValueError("Use 1–20 windows, each at most eight seconds")
    context_file = Path(segments_csv).with_name("round_context.csv")
    excluded = set()
    if context_file.is_file():
        excluded = {
            row["timestamp_ms"]
            for row in read_table(context_file)
            if row["phase"]
            in {
                "buy_phase",
                "buy_phase_candidate",
                "technical_pause",
                "tactical_timeout",
                "pause_or_halftime",
                "round_end_candidate",
                "replay",
            }
        }
    rows = []
    last_end = -1
    for row in read_table(segments_csv):
        if row["segment_type"] != "gameplay" or row["processing_action"] != "extract":
            continue
        if row["timestamp_ms"] in excluded:
            continue
        center = float(row["timestamp_ms"]) / 1000
        start = max(0, center - seconds / 2)
        if start < last_end:
            continue
        rows.append({"start_seconds": start, "end_seconds": start + seconds})
        last_end = start + seconds + 10
        if len(rows) == limit:
            break
    return rows


def extract_windows(source, output_dir, windows, expected_sha256=None):
    """Decode original presentation timestamps with PyAV; no FPS conversion.

    Each completed window is immutable and resumable. A decode/frame-limit failure
    never publishes a partial window. Input size is bounded for a free notebook.
    """
    import av

    from .pipeline import sha256

    if not 1 <= len(windows) <= 20:
        raise ValueError("Select 1–20 bounded windows")
    normalized = []
    for window in windows:
        start, end = float(window["start_seconds"]), float(window["end_seconds"])
        if not all(map(math.isfinite, [start, end])) or start < 0 or not 0 < end - start <= 8:
            raise ValueError("Windows must be finite, nonnegative and at most eight seconds")
        normalized.append((start, end))
    source_hash = sha256(source)
    if expected_sha256 and source_hash != expected_sha256:
        raise ValueError("Source checksum differs from extraction manifest")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifests = []
    for start, end in normalized:
        identity = {
            "source_sha256": source_hash,
            "start_seconds": start,
            "end_seconds": end,
            "schema_version": VERSION,
            "pyav_version": av.__version__,
        }
        key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:24]
        folder = output_dir / key
        if (folder / "manifest.json").is_file():
            if json.loads((folder / "manifest.json").read_text()) != identity:
                raise ValueError("Window cache identity mismatch")
            cached = read_table(folder / "frames.csv")
            if not cached or any(not (folder / row["image_path"]).is_file() for row in cached):
                raise ValueError("Incomplete window cache; restore or remove this window")
            manifests.append(folder / "frames.csv")
            continue
        temporary = output_dir / (key + ".partial")
        temporary.mkdir(exist_ok=True)
        rows = []
        try:
            with av.open(str(source)) as container:
                stream = container.streams.video[0]
                origin = float(stream.start_time * stream.time_base) if stream.start_time else 0.0
                container.seek(int((start + origin) / stream.time_base), stream=stream)
                previous = None
                for frame in container.decode(stream):
                    if frame.pts is None:
                        raise ValueError("Missing presentation timestamp; cannot measure timing")
                    timestamp = float(frame.pts * frame.time_base) - origin
                    if timestamp < start:
                        continue
                    if timestamp >= end:
                        break
                    if previous is not None and timestamp <= previous:
                        raise ValueError("Non-increasing presentation timestamps")
                    previous = timestamp
                    if len(rows) >= 1000:
                        raise ValueError("Window exceeds 1000-frame safety limit")
                    index = len(rows)
                    name = f"frame_{index:05d}.jpg"
                    frame.to_image().save(temporary / name, quality=90)
                    rows.append(
                        {
                            "frame_id": f"{key}:{index}",
                            "window_id": key,
                            "source_sha256": source_hash,
                            "pts": frame.pts,
                            "time_base": str(frame.time_base),
                            "timestamp_ms": timestamp * 1000,
                            "image_path": name,
                            "schema_version": VERSION,
                        }
                    )
            if len(rows) < 2:
                raise ValueError("Window contains fewer than two decoded frames")
            write_table(temporary / "frames.csv", rows, list(rows[0]))
            (temporary / "manifest.json").write_text(
                json.dumps(identity, indent=2), encoding="utf-8"
            )
            if folder.exists():
                raise ValueError("Incomplete destination window already exists")
            temporary.rename(folder)
        except Exception:
            # Only the verified child created for this bounded window is removed.
            if temporary.parent.resolve() == output_dir.resolve():
                shutil.rmtree(temporary)
            raise
        manifests.append(folder / "frames.csv")
    # Never overwrite a user's annotations on rerun.
    template = output_dir / "pov_events_to_review.csv"
    if not template.exists():
        write_table(
            template,
            [
                dict.fromkeys(EVENT_FIELDS, "")
                | {
                    "window_id": path.parent.name,
                    "review_status": "unreviewed",
                    "earlier_cues_unknown": "true",
                }
                for path in manifests
            ],
            EVENT_FIELDS,
        )
    return manifests


def export_timings(events_csv, frame_manifests, destination):
    """Only reviewed, continuous player POV evidence yields a numeric latency.

    Temporal bounds bracket the first visible cue/action using preceding frames.
    They describe video sampling uncertainty, not physiological reaction time.
    """
    frames, previous = {}, {}
    for manifest in frame_manifests:
        prior = None
        for row in read_table(manifest):
            key = row["frame_id"]
            stamp = float(row["timestamp_ms"])
            if (
                key in frames
                or not math.isfinite(stamp)
                or (prior and stamp <= float(prior["timestamp_ms"]))
            ):
                raise ValueError("Duplicate frame ID or invalid frame timeline")
            frames[key] = row
            previous[key] = prior
            prior = row
    results, seen = [], set()
    for event in read_table(events_csv):
        if not event.get("event_id"):
            continue  # Untouched template row.
        if event["event_id"] in seen:
            raise ValueError("Duplicate event ID")
        seen.add(event["event_id"])
        reason = ""
        cue, action = frames.get(event["cue_frame_id"]), frames.get(event["action_frame_id"])
        checks = [
            "player_identity_verified",
            "xray_absent",
            "continuous_view",
            "cue_visibility_verified",
        ]
        if event["review_status"] != "reviewed" or not event["reviewer_id"]:
            reason = "independent_review_required"
        elif not event["player_id"] or event["perspective"] != "player_pov":
            reason = "unknown_player_or_non_player_pov"
        elif any(event[name] != "true" for name in checks):
            reason = "visibility_or_continuity_not_verified"
        elif event["cue_type"] != "enemy_first_visible" or event["action_type"] not in {
            "shot",
            "ability",
            "disengage",
        }:
            reason = "unsupported_event_type"
        elif not cue or not action:
            reason = "missing_frame_evidence"
        elif (
            any(row["window_id"] != event["window_id"] for row in [cue, action])
            or cue["source_sha256"] != action["source_sha256"]
        ):
            reason = "evidence_source_or_window_mismatch"
        elif not previous[cue["frame_id"]] or not previous[action["frame_id"]]:
            reason = "onset_not_bracketed_by_previous_frame"
        elif float(action["timestamp_ms"]) < float(cue["timestamp_ms"]):
            reason = "action_precedes_cue"
        result = {name: event.get(name, "") for name in EVENT_FIELDS}
        result.update(
            source_sha256=cue["source_sha256"] if cue else "",
            latency_ms="",
            latency_lower_ms="",
            latency_upper_ms="",
            measurement_status="insufficient_evidence",
            exclusion_reason=reason,
            metric="visible_cue_to_action_latency",
            schema_version=VERSION,
        )
        if not reason:
            cue_ms, action_ms = float(cue["timestamp_ms"]), float(action["timestamp_ms"])
            result.update(
                latency_ms=action_ms - cue_ms,
                latency_lower_ms=max(
                    0, float(previous[action["frame_id"]]["timestamp_ms"]) - cue_ms
                ),
                latency_upper_ms=action_ms - float(previous[cue["frame_id"]]["timestamp_ms"]),
                measurement_status="reviewed_video_estimate",
            )
        results.append(result)
    fields = EVENT_FIELDS + [
        "source_sha256",
        "latency_ms",
        "latency_lower_ms",
        "latency_upper_ms",
        "measurement_status",
        "exclusion_reason",
        "metric",
        "schema_version",
    ]
    return write_table(destination, results, fields)
