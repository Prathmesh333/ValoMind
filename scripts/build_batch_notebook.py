"""Build a standalone, persistent single-GPU full-broadcast collector."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
modules = {
    p.name: p.read_text(encoding="utf-8")
    for p in (ROOT / "workers/analysis/valomind_video").glob("*.py")
}
sources = json.loads((ROOT / "configs/vct_playoffs_sources.json").read_text())["sources"]
cells = []


def cell(kind, source):
    row = {"cell_type": kind, "metadata": {}, "source": source.splitlines(keepends=True)}
    if kind == "code":
        row.update(execution_count=None, outputs=[])
    cells.append(row)


cell(
    "markdown",
    """# ValoMind: five full VCT playoff broadcasts on one T4
Run all cells. The queue collects proposed OCR/HUD context and unlabeled review samples
from five official archived Champions Seoul 2024 broadcasts (4h44m–6h37m; ~27h20m total).
It does **not** train a model, infer thoughts, or claim verified player/agent identities.

Colab: select Runtime → Change runtime type → T4 GPU. Drive stores metadata, SQLite
checkpoints and images; only the current full video uses temporary Colab disk.
Run the queue cell again after its budget expires. After a disconnect, rerun setup/config
with the same RUN_NAME and parameters. Never run two notebooks against the same queue root.
Free GPU availability, runtime duration and YouTube access are not guaranteed.

New broadcasts have no reviewed player catalog/HUD calibration. Empty roster exports are
expected until those are supplied. Full-frame OCR and review images still provide data.
""",
)
cell(
    "code",
    """import sys, subprocess, json, hashlib, math, shutil, csv
from pathlib import Path
subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', '-q',
    'yt-dlp[default]>=2026.1', 'opencv-python-headless>=4.10,<5',
    'easyocr>=1.7,<2', 'ultralytics>=8.3,<9'], check=True)
if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
    raise RuntimeError('This runtime needs ffmpeg and ffprobe.')
"""
    + f"MODULES = {modules!r}\n"
    + """package = Path('/tmp/valomind_batch_worker/valomind_video')
package.mkdir(parents=True, exist_ok=True)
for name, source in MODULES.items():
    (package / name).write_text(source, encoding='utf-8')
sys.path.insert(0, str(package.parent))
for name in list(sys.modules):
    if name == 'valomind_video' or name.startswith('valomind_video.'):
        del sys.modules[name]
from valomind_video.pipeline import process, download, VERSION
from valomind_video.batch import run_queue, atomic_json, validate_sources, OFFICIAL_CHANNEL
from valomind_video.acquisition import ensure_runtime, cached_video, restore_source_archive, youtube_options
from valomind_video.pov import read_table, write_table
JS_RUNTIME = ensure_runtime()
WORKER_HASH = hashlib.sha256(json.dumps(MODULES, sort_keys=True).encode()).hexdigest()
import torch
import importlib.metadata
if not torch.cuda.is_available():
    raise RuntimeError('Select a T4 GPU in runtime settings before continuing.')
torch.cuda.set_device(0)
DEVICE = '0'
print('Using only CUDA GPU 0:', torch.cuda.get_device_name(0))
probe = torch.ones(1, device='cuda:0') * 2
torch.cuda.synchronize(0)
assert probe.item() == 2
del probe
""",
)
cell(
    "code",
    """# Keep these values unchanged to resume. New parameters require a new RUN_NAME.
RUN_NAME = 'seoul_playoffs_batch_v1'
IS_KAGGLE = Path('/kaggle').exists()
if IS_KAGGLE:
    # Kaggle: Save Version with outputs; /kaggle/working is NOT durable across fresh sessions.
    PERSISTENT_ROOT = Path('/kaggle/working/ValoMind')
    MEDIA_ROOT = Path('/kaggle/temp/valomind_media')
else:
    from google.colab import drive
    drive.mount('/content/drive')
    PERSISTENT_ROOT = Path('/content/drive/MyDrive/ValoMind')
    MEDIA_ROOT = Path('/content/valomind_media')
WORK_ROOT = PERSISTENT_ROOT / RUN_NAME
WORK_ROOT.mkdir(parents=True, exist_ok=True)
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

INTERVAL_SECONDS = 10.0  # Sparse scan of the ENTIRE broadcast, not a two-minute preview.
CHUNK_SAMPLES = 100  # Checkpoint after at most 100 additional probes per worker call.
RUN_BUDGET_MINUTES = 90  # Checked between chunks; a download/chunk can exceed this budget.
REVIEW_IMAGES_PER_VIDEO = 240  # Spread over the broadcast, includes filler/unknown samples.
PURGE_TEMP_VIDEO_AFTER_COMPLETION = True  # Only completed, managed temporary video files.
DENSE_WINDOWS_PER_VIDEO = 0  # Optional 1–2 two-second native-frame windows; adds image storage.
COOKIE_FILE = None  # Own authorized Netscape cookies, outside WORK_ROOT and MEDIA_ROOT.
RETRY_ERRORS = False  # Set True only AFTER fixing sign-in/storage/runtime errors, then return False.
SOURCE_ARCHIVES = {}  # Optional {video_id: '/content/drive/MyDrive/<source_archive>.zip'}.
# The old highlight ZIP cannot restore any of these new videos.
ROSTER_CATALOGS = {}  # Optional per-video reviewed aliases/layout-compatible catalog. No global 100T/VIT aliases.
if COOKIE_FILE:
    cookie_path = Path(COOKIE_FILE).resolve()
    if cookie_path.is_relative_to(WORK_ROOT.resolve()) or cookie_path.is_relative_to(MEDIA_ROOT.resolve()):
        raise ValueError('Keep cookies outside both export and temporary-media roots.')
if DENSE_WINDOWS_PER_VIDEO not in {0, 1, 2}:
    raise ValueError('Dense windows must be 0, 1, or 2.')
if DENSE_WINDOWS_PER_VIDEO:
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'av>=14,<17'], check=True)
"""
    + f"SOURCES = {sources!r}\n"
    + """# To assign this notebook a subset, use e.g. SOURCES = SOURCES[:1] and a different RUN_NAME.
validate_sources(SOURCES)
atomic_json(WORK_ROOT / 'source_catalog.json', {'sources': SOURCES})
(WORK_ROOT / 'environment.txt').write_text(
    subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True), encoding='utf-8')
for source in SOURCES:
    seconds = source['duration_seconds']
    print(source['video_id'], f'{seconds//3600}:{seconds//60%60:02d}:{seconds%60:02d}',
          source['dataset_role'], source['title'])
print('Persistent output:', WORK_ROOT)
print('Temporary videos:', MEDIA_ROOT)
""",
)
cell(
    "markdown",
    """## Acquisition and continuation
The next cell downloads one archive at a time, processes bounded chunks, and keeps the
same source active until it finishes or the run budget ends. Completed jobs are skipped.
If YouTube requests verification, the queue stops and records the error instead of retrying
other accounts, proxies or all five URLs. Configure your own authorized cookies or restore
the matching source archive from Drive; then explicitly enable RETRY_ERRORS once.

YouTube metadata/channel IDs are checked again at runtime. The 2024 roster/HUD has not
been calibrated against our earlier video. Unknown identities remain unknown; raw OCR,
probe decisions and uniformly sampled review images are the initial collection targets.
""",
)
cell(
    "code",
    """def validate_metadata(info, source):
    if info.get('id') != source['video_id'] or info.get('channel_id') != OFFICIAL_CHANNEL:
        raise ValueError('Video metadata does not match the selected official source.')
    if info.get('is_live') or info.get('live_status') == 'is_live':
        raise ValueError('Wait for the livestream to finish; archived videos only.')
    duration = float(info.get('duration') or 0)
    if not duration or abs(duration - source['duration_seconds']) > max(5, duration * 0.01):
        raise ValueError('Source duration changed materially; inspect before processing.')


def collect_review_samples(output, source):
    from PIL import Image
    rows = []
    for segment in read_table(output.parent / 'segments.csv'):
        details = json.loads(segment['text'])
        relative = details.get('review_image')
        if not relative:
            continue
        image_path = (output.parent / relative).resolve()
        if not image_path.is_relative_to(output.parent.resolve()) or not image_path.is_file():
            continue
        crop = output.parent / 'minimap_candidates' / image_path.name
        crop.parent.mkdir(exist_ok=True)
        with Image.open(image_path) as image:
            width, height = image.size
            image.crop((0, round(height*0.04), round(width*0.24), round(height*0.36))).save(crop, quality=95)
        rows.append({'sample_id': segment['observation_id'], 'video_id': source['video_id'],
                     'source_sha256': segment['source_sha256'], 'timestamp_ms': segment['timestamp_ms'],
                     'image': relative, 'segment_suggestion': segment['segment_type'],
                     'dataset_role': source['dataset_role'], 'source_group': source['video_id'],
                     'label': '', 'review_status': 'unreviewed', 'reviewer_id': '',
                     'training_eligible': 'false', 'player_id': '', 'team_id': '',
                     'character_agent_id': '', 'map_id': '',
                     'minimap_candidate': str(crop.relative_to(output.parent)).replace('\\\\','/'),
                     'crop_review_status': 'unreviewed_uncalibrated_region'})
    fields = list(rows[0]) if rows else ['sample_id', 'video_id', 'image', 'review_status']
    write_table(output.parent / 'unlabeled_samples.csv', rows, fields)
    atomic_json(output.parent / 'collection_summary.json', {
        'video_id': source['video_id'], 'review_images': len(rows),
        'reviewed_player_catalog_supplied': bool(ROSTER_CATALOGS.get(source['video_id'])),
        'identity_status': 'proposals_only' if ROSTER_CATALOGS.get(source['video_id']) else 'unknown_no_reviewed_catalog',
        'dataset_role': source['dataset_role'], 'training_performed': False})


def worker(source):
    key = source['video_id']
    if key in SOURCE_ARCHIVES:
        restore_source_archive(SOURCE_ARCHIVES[key], MEDIA_ROOT, key)
    folder = MEDIA_ROOT / 'sources' / key
    video = cached_video(folder, key)
    if video:
        info = json.loads((folder / 'video.info.json').read_text(encoding='utf-8'))
        validate_metadata(info, source)
    else:
        if shutil.disk_usage(MEDIA_ROOT).free < 30 * 2**30:
            raise RuntimeError('Less than 30 GiB free temporary disk. Free space before downloading.')
        from yt_dlp import YoutubeDL
        from yt_dlp.utils import DownloadError
        from valomind_video.acquisition import download_error_message
        try:
            options = {'skip_download': True, 'noplaylist': True,
                       **youtube_options(COOKIE_FILE, JS_RUNTIME, MEDIA_ROOT)}
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(source['url'], download=False)
        except DownloadError as error:
            raise RuntimeError(download_error_message(error)) from None
        validate_metadata(info, source)
        video = download(source['url'], MEDIA_ROOT, cookie_file=COOKIE_FILE, js_runtime=JS_RUNTIME)
    stride = max(1, math.ceil(source['duration_seconds'] / INTERVAL_SECONDS / REVIEW_IMAGES_PER_VIDEO))
    output = process(source['url'], WORK_ROOT, media_root=MEDIA_ROOT, device=DEVICE,
                     cookie_file=COOKIE_FILE, js_runtime=JS_RUNTIME,
                     interval_seconds=INTERVAL_SECONDS, end_seconds=None,
                     sampling_mode='seek', max_new_samples=CHUNK_SAMPLES,
                     review_sample_limit=REVIEW_IMAGES_PER_VIDEO, review_every_samples=stride,
                     segment_filter=True, save_portrait_crops=False, crop_ocr_retry=False,
                     roster_catalog=ROSTER_CATALOGS.get(key))
    # Keep source metadata after the large temporary video is purged.
    shutil.copyfile(folder / 'video.info.json', output.parent / 'source_metadata.json')
    collect_review_samples(output, source)
    progress = json.loads((output.parent / 'progress.json').read_text())
    if progress['complete'] and DENSE_WINDOWS_PER_VIDEO:
        from valomind_video.pov import extract_windows
        candidates = [row for row in read_table(output.parent / 'segments.csv')
                      if row['segment_type'] == 'gameplay' and row['processing_action'] == 'extract']
        if candidates:
            indices = sorted({min(len(candidates)-1, int(len(candidates)*fraction))
                              for fraction in ([0.5] if DENSE_WINDOWS_PER_VIDEO == 1 else [0.25, 0.75])})
            windows = [{'start_seconds': max(0, float(candidates[index]['timestamp_ms'])/1000-1),
                        'end_seconds': max(0, float(candidates[index]['timestamp_ms'])/1000-1)+2}
                       for index in indices]
            extract_windows(video, output.parent / 'pov_review', windows,
                            expected_sha256=json.loads((output.parent/'manifest.json').read_text())['source_sha256'])
    if progress['complete'] and PURGE_TEMP_VIDEO_AFTER_COMPLETION:
        # Delete only managed ephemeral video files, never Drive outputs or user archives.
        allowed = Path('/kaggle/temp/valomind_media' if IS_KAGGLE else '/content/valomind_media').resolve()
        if MEDIA_ROOT.resolve() != allowed or not video.resolve().is_relative_to(allowed):
            raise ValueError('Refusing media cleanup outside the managed temporary root.')
        for suffix in ['.mp4', '.webm', '.mkv']:
            target = folder / ('video' + suffix)
            if target.is_file() and target.resolve().parent == folder.resolve():
                target.unlink()
    return {'output_csv': output, 'complete': progress['complete']}


CONFIGURATION = {'pipeline_version': VERSION, 'worker_hash': WORKER_HASH,
                 'ocr_packages': {name: importlib.metadata.version(name)
                                  for name in ['easyocr', 'opencv-python-headless']},
                 'interval_seconds': INTERVAL_SECONDS, 'review_limit': REVIEW_IMAGES_PER_VIDEO,
                 'sampling_mode': 'seek', 'roster_catalogs': ROSTER_CATALOGS,
                 'dense_windows': DENSE_WINDOWS_PER_VIDEO}
state = run_queue(SOURCES, WORK_ROOT, worker, CONFIGURATION,
                  budget_seconds=RUN_BUDGET_MINUTES*60, retry_errors=RETRY_ERRORS)
print(json.dumps(state, indent=2))
print('Rerun THIS cell to continue the same queue; do not change RUN_NAME or configuration.')
""",
)
cell(
    "markdown",
    """## Export partial or completed data
Run this cell whenever you want a snapshot, including after a queue error. It excludes
full source videos and cookies, retains per-job SQLite state and proposed labels, and
does not randomly split neighboring frames. Three broadcasts are train candidates,
one is reserved for validation, one for testing; no supervised training is performed.
Broadcast/source groups remain intact; confirm match identities before final evaluation.
""",
)
cell(
    "code",
    """# Collect only outputs recorded by this queue, not unrelated jobs in other runs.
from valomind_video.pipeline import merge
state = json.loads((WORK_ROOT / 'queue_status.json').read_text())
outputs = [WORK_ROOT / item['output_csv'] for item in state['jobs'].values()
           if item.get('output_csv') and (WORK_ROOT / item['output_csv']).is_file()]
if outputs:
    merge(outputs, WORK_ROOT / 'merged_observations.csv')
    for filename in ['round_context.csv', 'roster_observations.csv', 'unlabeled_samples.csv']:
        paths = [path.parent / filename for path in outputs if (path.parent / filename).is_file()]
        all_rows, fields = [], []
        for path in paths:
            with path.open(newline='', encoding='utf-8') as stream:
                reader = csv.DictReader(stream)
                fields = list(dict.fromkeys(fields + (reader.fieldnames or [])))
                all_rows.extend(reader)
        if fields:
            write_table(WORK_ROOT / ('combined_' + filename),
                        [{field: row.get(field, '') for field in fields} for row in all_rows], fields)
else:
    print('No completed worker chunk yet; archive still contains queue status for diagnosis.')
from zipfile import ZipFile, ZIP_DEFLATED
archive_dir = PERSISTENT_ROOT / 'exports'
archive_dir.mkdir(exist_ok=True)
archive = archive_dir / (RUN_NAME + '_results.zip')
with ZipFile(archive, 'w', compression=ZIP_DEFLATED) as bundle:
    for path in WORK_ROOT.rglob('*'):
        if not path.is_file() or path.suffix.lower() in {'.mp4', '.webm', '.mkv'}:
            continue
        if 'cookie' in path.name.lower() or path.name == '.env':
            continue
        bundle.write(path, path.relative_to(WORK_ROOT))
print('Snapshot:', archive, 'MiB:', round(archive.stat().st_size/2**20, 1))
# Drive already retains the archive. Set True if you also want a browser download.
DOWNLOAD_SNAPSHOT = False
if DOWNLOAD_SNAPSHOT and not IS_KAGGLE:
    from google.colab import files
    files.download(str(archive))
""",
)
notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
        "accelerator": "GPU",
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
(ROOT / "notebooks/VCT_playoffs_batch.ipynb").write_text(
    json.dumps(notebook, indent=2) + "\n", encoding="utf-8"
)
