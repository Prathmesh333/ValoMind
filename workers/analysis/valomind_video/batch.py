"""Persistent, bounded, single-worker broadcast queue. No accounts or GPU parallelism."""

import hashlib
import json
import math
import time
from pathlib import Path

from .pipeline import video_id

OFFICIAL_CHANNEL = "UCA1d3HFGFUmkKr2JIUA5Vlw"


def validate_sources(sources):
    if not 1 <= len(sources) <= 5:
        raise ValueError("Select one to five archived broadcasts")
    seen = set()
    for source in sources:
        key = video_id(source["url"])
        if key != source["video_id"] or key in seen:
            raise ValueError("Duplicate or mismatched source ID")
        seen.add(key)
        if source["channel_id"] != OFFICIAL_CHANNEL:
            raise ValueError("Expected the official VALORANT Champions Tour channel")
        if source.get("is_live_now") or not source.get("is_live_content"):
            raise ValueError("Use completed livestream archives, not active streams or highlights")
        if not 4 * 3600 <= source["duration_seconds"] <= 12 * 3600:
            raise ValueError("Expected a long broadcast between four and twelve hours")
        if source["dataset_role"] not in {"train_proposed", "validation_reserved", "test_reserved"}:
            raise ValueError("Unknown dataset role")
    return sources


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def run_queue(
    sources,
    root,
    worker,
    configuration,
    budget_seconds=5400,
    retry_errors=False,
    clock=time.monotonic,
):
    """Worker returns a partial/completed output CSV. Checkpoints survive cell interruption.

    Budget is checked between worker chunks, not during downloads/inference. Only
    one notebook may own a queue root. Error retries require explicit configuration.
    """
    validate_sources(sources)
    if not math.isfinite(budget_seconds) or budget_seconds <= 0:
        raise ValueError("Positive finite runtime budget required")
    root = Path(root).resolve()
    path = root / "queue_status.json"
    signature = hashlib.sha256(
        json.dumps({"sources": sources, "configuration": configuration}, sort_keys=True).encode()
    ).hexdigest()
    if path.exists():
        state = json.loads(path.read_text(encoding="utf-8"))
        if state["signature"] != signature:
            raise ValueError(
                "Queue configuration changed. Use a new RUN_NAME/root to preserve old jobs"
            )
    else:
        state = {
            "schema_version": "broadcast_queue_v1",
            "signature": signature,
            "configuration": configuration,
            "jobs": {row["video_id"]: {"status": "pending", "chunks": 0} for row in sources},
        }
    if retry_errors:
        for record in state["jobs"].values():
            if record["status"] in {"failed", "blocked"}:
                record["status"] = "paused"
    for record in state["jobs"].values():
        if record["status"] == "complete":
            candidate = (root / record.get("output_csv", "")).resolve()
            if not candidate.is_relative_to(root) or not candidate.is_file():
                record["status"] = "paused"
    atomic_json(path, state)
    deadline = clock() + budget_seconds
    while clock() < deadline:
        if any(row["status"] in {"failed", "blocked"} for row in state["jobs"].values()):
            print(
                "Queue stopped on an error. Fix acquisition/configuration before enabling RETRY_ERRORS."
            )
            break
        source = next(
            (row for row in sources if state["jobs"][row["video_id"]]["status"] != "complete"), None
        )
        if source is None:
            break
        record = state["jobs"][source["video_id"]]
        record["status"] = "running"
        atomic_json(path, state)
        try:
            print("Processing", source["video_id"], source["title"], flush=True)
            result = worker(source)
            if not isinstance(result.get("complete"), bool):
                raise TypeError("Worker must explicitly report boolean completion")
            output = Path(result["output_csv"]).resolve()
            if not output.is_relative_to(root) or not output.is_file():
                raise ValueError("Worker output must exist inside this queue root")
            record.update(
                status="complete" if result["complete"] else "paused",
                chunks=record["chunks"] + 1,
                output_csv=str(output.relative_to(root)).replace("\\", "/"),
                complete=bool(result["complete"]),
            )
            print(source["video_id"], record["status"], "chunks", record["chunks"], flush=True)
        except Exception as error:  # noqa: BLE001 -- Persist worker errors; never silently retry.
            message = str(error)
            blocked = any(
                token in message.casefold()
                for token in ["sign-in", "sign in", "verification", "not a bot"]
            )
            record.update(
                status="blocked" if blocked else "failed",
                error_type=type(error).__name__,
                error=message[:1500],
            )
            print(record["status"], source["video_id"], message, flush=True)
        atomic_json(path, state)
    return state
