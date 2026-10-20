"""Build a standalone notebook containing the portable worker source."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
cells = []


def cell(kind, source):
    entry = {"cell_type": kind, "metadata": {}, "source": source.splitlines(keepends=True)}
    if kind == "code":
        entry.update(execution_count=None, outputs=[])
    cells.append(entry)


cell(
    "markdown",
    """# VCT: YouTube → cloud processing → CSV
Run setup, configure a URL and run extraction. No local video upload is needed.
OCR works immediately; custom YOLO weights and an alias catalog improve proposals.
All outputs need review. Training requires labeled frames and is a separate optional step.
Enable a GPU. Colab/Kaggle resources and YouTube downloads are not guaranteed.
""",
)
requirements = (ROOT / "notebooks/requirements-video.txt").read_text()
modules = {
    path.name: path.read_text(encoding="utf-8")
    for path in (ROOT / "workers/analysis/valomind_video").glob("*.py")
}
helpers = {
    name: (ROOT / "scripts" / name).read_text(encoding="utf-8")
    for name in ["prepare_portrait_dataset.py", "evaluate_segment_review.py"]
}
cell(
    "code",
    """import sys, subprocess, json
from pathlib import Path
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q',
    'yt-dlp[default]>=2026.1', 'opencv-python-headless>=4.10,<5',
    'easyocr>=1.7,<2', 'ultralytics>=8.3,<9'], check=True)
# ffmpeg is required by the downloader for merging video and audio.
import shutil
if shutil.which('ffmpeg') is None:
    raise RuntimeError('Install ffmpeg in this runtime before downloading.')
"""
    + f"modules = {modules!r}\n"
    + f"helpers = {helpers!r}\n"
    + """package = Path('/tmp/valomind_worker/valomind_video')
package.mkdir(parents=True, exist_ok=True)
for name, source in modules.items():
    (package / name).write_text(source, encoding='utf-8')
for name, source in helpers.items():
    (package.parent / name).write_text(source, encoding='utf-8')
sys.path.insert(0, str(package.parent))
for name in list(sys.modules):
    if name == 'valomind_video' or name.startswith('valomind_video.') or name in {
        'prepare_portrait_dataset', 'evaluate_segment_review'}:
        del sys.modules[name]
from valomind_video.pipeline import channel_videos, download, process, merge
from valomind_video.roster import export_rosters
from prepare_portrait_dataset import prepare as prepare_classifier_dataset
from evaluate_segment_review import evaluate as evaluate_segments
""",
)
cell(
    "code",
    """# Colab: optionally mount Drive first and set WORK_ROOT under /content/drive/MyDrive/.
# Kaggle: /kaggle/working/valomind is suitable for saved notebook outputs.
WORK_ROOT = Path('/kaggle/working/valomind' if Path('/kaggle').exists() else '/content/valomind')
WORK_ROOT.mkdir(parents=True, exist_ok=True)
SOURCE_URL = 'https://youtu.be/omjZXmc7_4A'
CHANNEL_SECTION = 'streams'  # 'videos' for uploads/highlights
LIST_LIMIT = 5
import torch
if not torch.cuda.is_available():
    raise RuntimeError('No CUDA GPU assigned. In Colab select Runtime > Change runtime type > T4 GPU, then rerun.')
torch.cuda.set_device(0)
DEVICE = '0'  # Exactly one GPU for YOLO inference/training; no multi-GPU list.
GPU_NAME = torch.cuda.get_device_name(0)
print('Using CUDA GPU 0:', GPU_NAME)
print('VRAM GiB:', round(torch.cuda.get_device_properties(0).total_memory / 2**30, 1))
if 'T4' not in GPU_NAME.upper():
    print('This runtime assigned a different GPU; only GPU 0 will be used.')
# Verify a CUDA operation before downloading the video.
probe = torch.ones(1, device='cuda:0') * 2
torch.cuda.synchronize(0)
assert probe.item() == 2
del probe
frozen = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True)
(WORK_ROOT / 'environment.txt').write_text(frozen)

if '/@' in SOURCE_URL:
    candidates = channel_videos(SOURCE_URL, limit=LIST_LIMIT, section=CHANNEL_SECTION)
    for index, item in enumerate(candidates):
        print(index, item['title'], item['url'])
    SELECTED_URLS = []  # Paste selected candidate URLs here, then run the extraction cell.
else:
    SELECTED_URLS = [SOURCE_URL]
""",
)
cell(
    "code",
    """# Configure this cell after inspecting the channel listing.
# SELECTED_URLS = ['https://www.youtube.com/watch?v=...']
WEIGHTS = None  # Path to custom best.pt. None runs OCR bootstrap only.
CATALOG = []  # e.g. {'kind':'player','id':'p1','aliases':['EXACT DISPLAY NAME']}
# Other kinds: team, map, character_agent. Use consistent IDs across notebooks.
INTERVAL_SECONDS = 2.0
END_SECONDS = 120  # Preview first; set None for the full video.
SEGMENT_FILTER = True  # Skip detected fillers/replays before full OCR and YOLO.
CONFIRM_SAMPLES = 2  # Weak HUD evidence needs consecutive samples; strong spatial HUD can admit one.
SAVE_PORTRAIT_CROPS = True  # Unlabeled roster portraits for review/classifier training.
ROSTER_CATALOG = None  # None uses the inspected video's scoped name/team aliases.
CROP_OCR_RETRY = True  # Retry unresolved team/name regions at 3x scale.
PORTRAIT_REFERENCE_CSV = None  # Reviewed portrait_review.csv from an extracted reference pack.
PORTRAIT_CLASSIFIER_WEIGHTS = None  # Trained character classifier best.pt; different from HUD WEIGHTS.
PORTRAIT_ALLOWED_CLASSES = None  # Defaults to the six inspected characters plus unknown.
ALLOW_PROPOSED_PORTRAIT_REFERENCES = False  # Diagnostic use only; never verifies outputs.
REVIEW_SAMPLE_LIMIT = 24  # All segment states: JPEGs sampled every fifth probe.
if not SELECTED_URLS:
    raise ValueError('Select one or more video URLs from the channel listing first.')
outputs = []
for url in SELECTED_URLS:
    output = process(url, WORK_ROOT, weights=WEIGHTS, device=DEVICE,
                     interval_seconds=INTERVAL_SECONDS, end_seconds=END_SECONDS,
                     catalog=CATALOG, segment_filter=SEGMENT_FILTER,
                     confirm_samples=CONFIRM_SAMPLES, save_portrait_crops=SAVE_PORTRAIT_CROPS,
                     roster_catalog=ROSTER_CATALOG, crop_ocr_retry=CROP_OCR_RETRY,
                     portrait_reference_csv=PORTRAIT_REFERENCE_CSV,
                     portrait_classifier_weights=PORTRAIT_CLASSIFIER_WEIGHTS,
                     portrait_allowed_classes=PORTRAIT_ALLOWED_CLASSES,
                     allow_proposed_portrait_references=ALLOW_PROPOSED_PORTRAIT_REFERENCES,
                     review_sample_limit=REVIEW_SAMPLE_LIMIT)
    outputs.append(output)
    print('Saved', output)
    print('Segment decisions:', output.parent / 'segments.csv')
    print('Player/team/map proposals:', output.parent / 'roster_observations.csv')
    if PORTRAIT_REFERENCE_CSV or PORTRAIT_CLASSIFIER_WEIGHTS:
        print('Agent proposals:', output.parent / 'roster_with_agents.csv')
    print('Segment review images:', output.parent / 'segment_review')
    print('Segment labeling queue:', output.parent / 'segment_review_suggestions.csv')
    import csv
    from collections import Counter
    with (output.parent / 'segments.csv').open(newline='', encoding='utf-8') as stream:
        decisions = list(csv.DictReader(stream))
    counts = Counter(row['segment_type'] for row in decisions)
    print('Sampled-frame decisions:', dict(counts))
    print('These are sampled-frame counts, not exact segment durations.')
    if not any(row['processing_action'] == 'extract' for row in decisions):
        print('No gameplay/roster extraction admitted. Inspect probe text in segments.csv; '
              'the preview may be an intro, or this HUD layout may need tuning.')
""",
)
cell(
    "markdown",
    """## Broadcast filtering
Filtering is enabled by default. An upper-HUD OCR probe looks for timer/score,
roster/selection labels, replay markers and break/desk messages. Strong same-frame
map-strip plus central timer/round evidence admits gameplay immediately; weaker
signals require consecutive samples. Filler and replay markers suppress
extraction immediately; unclear frames are recorded for review, not guessed.
`segments.csv` records every sampled decision and probe text. Replays are skipped
from the observation CSV, not automatically deduplicated when no replay marker is
visible. Unfamiliar layouts or unmarked roster screens can be missed. Review the
segment CSV before full runs; this is a heuristic baseline, not a trained segment
classifier. Timing resolution follows INTERVAL_SECONDS, not exact video cuts.
If needed, set SEGMENT_FILTER=False for a diagnostic unfiltered extraction.
The entire video is still downloaded and decoded; filtering reduces full-frame
OCR/detector work, not download size. Pending review frames retain probe text only.
The default URL is the user-selected one-hour highlight compilation. Start with
END_SECONDS=120, inspect the summary/segment CSV, then set END_SECONDS=None for
the full source. Highlight cuts may omit roster screens and distort behavior rates.
""",
)
cell(
    "markdown",
    """## Optional: create labeling frames, then train
This does not auto-label ground truth. Label the sampled images and prepare a
YOLO dataset YAML with separate train/validation partitions. Use different matches
for meaningful validation. Do not feed raw OCR output back as verified labels.
""",
)
cell(
    "code",
    """MAKE_LABELING_FRAMES = False
if MAKE_LABELING_FRAMES:
    import cv2
    url = SELECTED_URLS[0]
    video = download(url, WORK_ROOT)
    folder = WORK_ROOT / 'labeling' / video.parent.name
    folder.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video))
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        if not cap.isOpened() or fps <= 0:
            raise ValueError('Cannot decode source video')
        for second in range(0, 300, 5):
            cap.set(cv2.CAP_PROP_POS_MSEC, second * 1000)
            ok, frame = cap.read()
            if not ok:
                break
            if not cv2.imwrite(str(folder / f'{second*1000:09d}.jpg'), frame):
                raise RuntimeError('Could not save labeling frame')
    finally:
        cap.release()
    print('Label these images:', folder)
""",
)
cell(
    "code",
    """TRAIN = False
DATA_YAML = ''  # Prepared, reviewed YOLO labels required.
INITIAL_WEIGHTS = 'yolo11n.pt'
if TRAIN:
    from ultralytics import YOLO
    if not Path(DATA_YAML).is_file():
        raise ValueError('Provide a labeled YOLO dataset YAML')
    model = YOLO(INITIAL_WEIGHTS)
    model.train(data=DATA_YAML, epochs=30, imgsz=960, batch=4, device=DEVICE, amp=True,
                seed=42, project=str(WORK_ROOT / 'training'), name='hud', exist_ok=False)
    print('Use the reported best.pt path as WEIGHTS for extraction.')
""",
)
cell(
    "markdown",
    """## Optional: train the separate character classifier
Use a reviewed dataset with train/character and val/character folders. Keep whole
videos/matches in one partition. scripts/prepare_portrait_dataset.py validates
source splits and excludes pending labels. The current 20-image assistant pack
is not independently reviewed and is not a generalization benchmark. The simple
reference matcher is diagnostic: its first cross-layout check abstained on all
10 query portraits. Do not lower its thresholds just to fill agent fields.
""",
)
cell(
    "code",
    """TRAIN_PORTRAITS = False
PORTRAIT_DATASET = ''  # Reviewed, source-separated classification dataset directory.
PREPARE_PORTRAIT_DATASET = False
PORTRAIT_REVIEW_CSV = ''  # Reviewed CSV with explicit source-separated split column.
if PREPARE_PORTRAIT_DATASET:
    prepare_classifier_dataset(PORTRAIT_REVIEW_CSV, PORTRAIT_DATASET)
if TRAIN_PORTRAITS:
    from ultralytics import YOLO
    data_root = Path(PORTRAIT_DATASET)
    if not (data_root / 'dataset_manifest.json').is_file():
        raise ValueError('Prepare the reviewed dataset and manifest first.')
    classifier = YOLO('yolo11n-cls.pt')
    classifier.train(data=str(data_root), epochs=30, imgsz=224, batch=16,
                     device=DEVICE, amp=True, seed=42,
                     project=str(WORK_ROOT / 'portrait_training'), name='characters', exist_ok=False)
    print('Use the reported best.pt as PORTRAIT_CLASSIFIER_WEIGHTS, not WEIGHTS.')
""",
)
cell(
    "code",
    """# Optional evaluation after independently labeling saved segment samples.
SEGMENT_REVIEW_LABELS = None  # Copy suggestions to segment_review_labels.csv before editing.
if SEGMENT_REVIEW_LABELS:
    import csv
    with Path(SEGMENT_REVIEW_LABELS).open(newline='', encoding='utf-8') as stream:
        report = evaluate_segments(list(csv.DictReader(stream)))
    print(json.dumps(report, indent=2))
    Path(SEGMENT_REVIEW_LABELS).with_suffix('.evaluation.json').write_text(json.dumps(report, indent=2))

# Merge CSV exports copied from independent notebooks, then download the archive.
csv_files = sorted((WORK_ROOT / 'jobs').glob('*/observations.csv'))
if not csv_files:
    raise ValueError('No extraction output to export')
merged = merge(csv_files, WORK_ROOT / 'merged_observations.csv')
export_rosters(merged, WORK_ROOT / 'merged_roster_observations.csv', catalog=ROSTER_CATALOG)
from zipfile import ZipFile, ZIP_DEFLATED
archive = WORK_ROOT.parent / 'valomind_results.zip'
# Export metadata/state only; the downloaded video made the first archive 1.6 GB.
INCLUDE_SOURCE_VIDEO = False
with ZipFile(archive, 'w', compression=ZIP_DEFLATED) as bundle:
    for path in WORK_ROOT.rglob('*'):
        if not path.is_file():
            continue
        if not INCLUDE_SOURCE_VIDEO and path.suffix.lower() in {'.mp4', '.webm', '.mkv'}:
            continue
        bundle.write(path, path.relative_to(WORK_ROOT))
print('Merged CSV:', merged, '\\nArchive:', archive)
try:
    from google.colab import files
    files.download(str(archive))
except ImportError:
    print('Kaggle: save the notebook output or download the archive from Files.')
""",
)
notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
(ROOT / "notebooks/VCT_video_jobs.ipynb").write_text(
    json.dumps(notebook, indent=2) + "\n", encoding="utf-8"
)
