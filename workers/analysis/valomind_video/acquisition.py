"""Supported JS runtime setup and bounded, explicit YouTube authentication options."""

import hashlib
import io
import json
import os
import platform
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path
from zipfile import ZipFile


def detect_runtime():
    for name, minimum in [("deno", (2, 3, 0)), ("node", (22, 0, 0))]:
        executable = shutil.which(name)
        if not executable:
            continue
        try:
            version = subprocess.check_output([executable, "--version"], text=True, timeout=10)
            match = re.search(r"(\d+)\.(\d+)\.(\d+)", version)
            if match and tuple(map(int, match.groups())) >= minimum:
                return {name: {"path": executable}}
        except (OSError, subprocess.SubprocessError):
            continue
    return {}


def ensure_runtime():
    """Install the official Deno Linux binary in the notebook, checking its asset digest."""
    found = detect_runtime()
    if found:
        return found
    if platform.system() != "Linux" or platform.machine() not in {"x86_64", "AMD64"}:
        raise RuntimeError("Install Deno >=2.3 or Node >=22 and rerun setup")
    request = urllib.request.Request(
        "https://api.github.com/repos/denoland/deno/releases/latest",
        headers={"User-Agent": "ValoMind-notebook"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        release = json.load(response)
    asset = next(
        (item for item in release["assets"] if item["name"] == "deno-x86_64-unknown-linux-gnu.zip"),
        None,
    )
    if not asset or not str(asset.get("digest", "")).startswith("sha256:"):
        raise RuntimeError("Official Deno asset has no verification digest; install Deno manually")
    url = asset["browser_download_url"]
    if not url.startswith("https://github.com/denoland/deno/releases/download/"):
        raise RuntimeError("Unexpected Deno release asset location")
    with urllib.request.urlopen(url, timeout=120) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != asset["digest"].split(":", 1)[1]:
        raise RuntimeError("Deno asset checksum mismatch")
    target = Path.home() / ".local/bin/deno"
    target.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(io.BytesIO(data)) as archive:
        binary = archive.read("deno")
    temporary = target.with_suffix(".tmp")
    temporary.write_bytes(binary)
    temporary.chmod(0o755)
    temporary.replace(target)
    os.environ["PATH"] = str(target.parent) + os.pathsep + os.environ.get("PATH", "")
    found = detect_runtime()
    if not found:
        raise RuntimeError("Deno installation did not pass the runtime version check")
    return found


def youtube_options(cookie_file=None, js_runtime=None, export_root=None):
    options = {"js_runtimes": js_runtime or detect_runtime()}
    if cookie_file:
        path = Path(cookie_file).expanduser().resolve()
        if not path.is_file():
            raise ValueError("COOKIE_FILE does not exist in this cloud runtime")
        if export_root and path.is_relative_to(Path(export_root).resolve()):
            raise ValueError(
                "Keep COOKIE_FILE outside WORK_ROOT so it cannot enter result archives"
            )
        options["cookiefile"] = str(path)
    return options


def download_error_message(error):
    message = str(error).casefold()
    if "not a bot" in message or "sign in to confirm" in message:
        return (
            "YouTube requires sign-in/verification from this cloud runtime. The JS runtime "
            "alone cannot guarantee access. Stop retrying; optionally configure COOKIE_FILE "
            "from your own authorized browser session outside WORK_ROOT, or reuse the "
            "previously downloaded video in persistent cloud storage. Never paste cookies "
            "into chat or commit them. No automatic proxy/account rotation is attempted."
        )
    return "YouTube acquisition failed. Check video availability, runtime setup and the downloader logs."


def cached_video(folder, key):
    """Reuse only a decodable completed video with matching stored source metadata."""
    info = folder / "video.info.json"
    if not info.is_file():
        return None
    try:
        metadata = json.loads(info.read_text(encoding="utf-8"))
        if metadata.get("id") != key or not shutil.which("ffprobe"):
            return None
        for suffix in [".mp4", ".webm", ".mkv"]:
            video = folder / ("video" + suffix)
            if not video.is_file() or video.stat().st_size == 0:
                continue
            probe = subprocess.check_output(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "json",
                    str(video),
                ],
                text=True,
                timeout=30,
            )
            duration = float(json.loads(probe)["format"]["duration"])
            expected = float(metadata.get("duration") or 0)
            if duration > 0 and (
                not expected or abs(duration - expected) <= max(2, expected * 0.01)
            ):
                return video
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        return None
    return None
