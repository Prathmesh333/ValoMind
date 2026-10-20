import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "workers/analysis"))

from valomind_video.acquisition import (
    cached_video,
    detect_runtime,
    download_error_message,
    restore_source_archive,
    youtube_options,
)
from valomind_video.pipeline import download


def test_supported_node_is_explicitly_enabled(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/node" if name == "node" else None)
    monkeypatch.setattr("subprocess.check_output", lambda *a, **kw: "v22.1.0")
    assert detect_runtime() == {"node": {"path": "/usr/bin/node"}}
    monkeypatch.setattr("subprocess.check_output", lambda *a, **kw: "v20.0.0")
    assert detect_runtime() == {}


def test_cookie_file_never_lives_in_export_root(tmp_path):
    private = tmp_path / "private_cookies.txt"
    private.write_text("synthetic test cookie file", encoding="utf-8")
    options = youtube_options(private, {"deno": {"path": "/bin/deno"}}, tmp_path / "exports")
    assert options["cookiefile"] == str(private.resolve())
    with pytest.raises(ValueError, match="outside WORK_ROOT"):
        youtube_options(private, export_root=tmp_path)


def test_cached_completed_video_does_not_need_youtube(tmp_path, monkeypatch):
    (tmp_path / "video.info.json").write_text(json.dumps({"id": "abcdefghijk", "duration": 120}))
    video = tmp_path / "video.mp4"
    video.write_bytes(b"synthetic decoder fixture")
    monkeypatch.setattr("shutil.which", lambda name: "/bin/ffprobe")
    monkeypatch.setattr(
        "subprocess.check_output", lambda *a, **kw: json.dumps({"format": {"duration": "120.0"}})
    )
    assert cached_video(tmp_path, "abcdefghijk") == video
    assert cached_video(tmp_path, "other_id") is None
    monkeypatch.setattr(
        "subprocess.check_output", lambda *a, **kw: json.dumps({"format": {"duration": "50.0"}})
    )
    assert cached_video(tmp_path, "abcdefghijk") is None


def test_authentication_error_is_actionable_without_echoing_private_details():
    message = download_error_message(
        Exception("Sign in to confirm you’re not a bot secret_session_value")
    )
    assert "COOKIE_FILE" in message
    assert "secret_session_value" not in message


def test_downloader_passes_runtime_and_stops_on_auth_failure(tmp_path, monkeypatch):
    class DownloadError(Exception):
        pass

    captured = {}

    class Downloader:
        def __init__(self, options):
            captured.update(options)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def extract_info(self, *args, **kwargs):
            raise DownloadError("Sign in to confirm you're not a bot")

    monkeypatch.setitem(sys.modules, "yt_dlp", SimpleNamespace(YoutubeDL=Downloader))
    monkeypatch.setitem(sys.modules, "yt_dlp.utils", SimpleNamespace(DownloadError=DownloadError))
    runtime = {"deno": {"path": "/bin/deno"}}
    with pytest.raises(RuntimeError, match="verification"):
        download("https://youtu.be/abcdefghijk", tmp_path, js_runtime=runtime)
    assert captured["js_runtimes"] == runtime
    assert "proxy" not in captured


def test_restore_prior_archive_checks_hash_and_only_restores_source(tmp_path, monkeypatch):
    import hashlib
    from zipfile import ZipFile

    key = "abcdefghijk"
    payload = b"synthetic completed video"
    archive = tmp_path / "prior.zip"
    with ZipFile(archive, "w") as bundle:
        bundle.writestr(f"sources/{key}/video.info.json", json.dumps({"id": key, "duration": 120}))
        bundle.writestr(f"sources/{key}/video.mp4", payload)
        bundle.writestr(
            "jobs/demo/manifest.json",
            json.dumps({"video_id": key, "source_sha256": hashlib.sha256(payload).hexdigest()}),
        )
        bundle.writestr("../../unwanted.txt", "do not extract")
    monkeypatch.setattr(
        "valomind_video.acquisition.cached_video",
        lambda folder, key: folder / "video.mp4" if (folder / "video.mp4").is_file() else None,
    )
    root = tmp_path / "work"
    result = restore_source_archive(archive, root, key)
    assert result.read_bytes() == payload
    assert sorted(
        str(path.relative_to(root)).replace("\\", "/") for path in root.rglob("*") if path.is_file()
    ) == [f"sources/{key}/video.info.json", f"sources/{key}/video.mp4"]


def test_metadata_only_archive_has_clear_recovery_error(tmp_path):
    from zipfile import ZipFile

    archive = tmp_path / "later.zip"
    with ZipFile(archive, "w") as bundle:
        bundle.writestr("results.csv", "header\n")
    with pytest.raises(ValueError, match="FIRST"):
        restore_source_archive(archive, tmp_path / "work", "abcdefghijk")


def test_restore_checksum_failure_does_not_commit_video(tmp_path, monkeypatch):
    from zipfile import ZipFile

    key = "abcdefghijk"
    archive = tmp_path / "bad.zip"
    with ZipFile(archive, "w") as bundle:
        bundle.writestr(f"sources/{key}/video.info.json", json.dumps({"id": key}))
        bundle.writestr(f"sources/{key}/video.mp4", b"corrupt")
        bundle.writestr(
            "jobs/demo/manifest.json", json.dumps({"video_id": key, "source_sha256": "0" * 64})
        )
    with pytest.raises(ValueError, match="checksum"):
        restore_source_archive(archive, tmp_path / "work", key)
    assert not list((tmp_path / "work").rglob("*.mp4"))
    assert not list((tmp_path / "work").rglob("*.part"))
