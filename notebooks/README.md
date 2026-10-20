# Colab / Kaggle video jobs

video_v5 fixes the observed gate misses: strong map-strip plus central clock/round
evidence admits gameplay in one sample; weak candidates retain confirmation. Probe
boxes are saved for spatial checking. The source-specific IQOT team alias recovers
the last five team blanks when reparsing existing OCR. See docs/FILTER_V5_FIXES.md.
The 55/60 saved-probe diagnostic is not a fresh cloud-run result.

video_v4 enables targeted crop OCR retry and exports sampled segment review images
plus segment_review_suggestions.csv. Portrait classification is optional: configure
PORTRAIT_CLASSIFIER_WEIGHTS for a trained character classifier, or
PORTRAIT_REFERENCE_CSV for reviewed diagnostic templates, never both. The template
baseline abstained on all ten cross-layout test portraits; it is not production
recognition. See docs/EXTRACTION_IMPROVEMENTS.md for dataset preparation, review
requirements, new outputs and the still-pending independent validation run.

video_v3 adds spatial roster CSVs and unlabeled agent-portrait crops for the two
inspected layouts. The default alias catalog is scoped to omjZXmc7_4A. It reads
CURRENT map separately from NEXT and normalizes 100T OCR only in its team-name
region. Unknown teams/picks stay blank. Configure ROSTER_CATALOG for other videos;
layout generalization is not yet established. See docs/ROSTER_EXTRACTION.md.
Old CSVs can be reprocessed locally without another GPU run using
scripts/parse_roster_export.py. Do not merge video_v2 and video_v3 observation schemas.

First real export exposed a strict HUD gate: all 60 preview samples were uncertain.
The rebuilt notebook includes hud_rules_v2 for VCT map-order/round signatures and
period-separated OCR timers. See docs/FIRST_BROADCAST_REVIEW.md. Re-upload this
notebook to Colab and restart the runtime before rerunning the preview. Do not use
the old notebook's embedded worker modules. Results archives now omit source
videos by default; retain cloud storage separately if you want to avoid re-download.

The notebook requires CUDA and explicitly selects GPU 0. In Colab select Runtime
→ Change runtime type → T4 GPU before running. It prints GPU name/VRAM and runs a
small CUDA operation before acquisition; missing CUDA stops execution rather than
falling back silently to CPU. EasyOCR uses cuda:0 and YOLO uses device=0. Optional
training starts with batch=4 and AMP enabled as a conservative T4 starting point,
not a measured memory guarantee. Download, video decoding and CSV export use CPU.
Colab controls GPU availability; the notebook cannot allocate or guarantee a T4.

Broadcast filtering is enabled by default. A small upper-HUD OCR probe looks for
timer/two-score patterns, roster/selection labels, replay markers and explicit
break/desk messages. Two consecutive gameplay/roster samples enable full-frame
OCR and detector extraction. Detected fillers/replays skip that work immediately.
Unknown frames retain probe text for review in `segments.csv`; they do not become
gameplay observations. Replays without a visible marker can still be missed.

This is an uncalibrated rule baseline, not a trained broadcast classifier. Review
the segment CSV for the selected layout before processing full broadcasts. A
roster screen without a recognized label or a match HUD with failed OCR may be
marked uncertain and omitted from full extraction. Filtering still downloads and
decodes the video; it reduces extraction work rather than download size. Set
SEGMENT_FILTER=False for diagnostic unfiltered runs. video_v2 job IDs and CSV
fields differ from video_v1; regenerate old outputs instead of mixing schemas.

Open `VCT_video_jobs.ipynb` in Colab (File → Upload notebook), or import it into
Kaggle. The notebook embeds this project's lightweight worker modules, so a Git
checkout or local video upload is unnecessary. Enable a GPU and internet access.
Setup installs yt-dlp, EasyOCR and Ultralytics; runtime package versions are saved.

Provide a video URL, or the official channel URL. Channel mode lists a bounded
number of uploads or streams. Choose the listed URLs to process; no archive-wide
download is automatic. Processing downloads into cloud runtime storage, runs
sampled OCR and optional custom YOLO detection, and exports CSV proposals.

The OCR bootstrap works without a trained detector. An alias catalog distinguishes
player/team/map/character mentions; it does not establish roster relationships.
Aliases use exact normalized whole-text matching and ambiguity causes abstention.
Names split across OCR regions or prefixed by team tags need catalog variants or
later layout-specific parsing. No default list of real players is invented.

For a first detector, sample frames using the optional cell, label HUD regions in
YOLO format, and supply a dataset YAML to the optional training cell. Typical
classes: player_card, team_name, agent_portrait, map_name, roster_row. Detecting an
agent_portrait region does not identify the character; portrait classification is
a separate future step. Adjacent frames from one video are not an independent
validation set. One video's training result is a smoke test, not a general model.

Each video/config/checkpoint/catalog combination has a separate SQLite job state
and CSV. Completed sampled frames are skipped on rerun, including frames without
detections. Different notebooks should use different video URLs and separate job
directories, then merge exported CSVs. Exact duplicates are removed; conflicting
rows are rejected. Different model versions remain distinct observations.

Cloud runtimes can disappear. Set WORK_ROOT to persistent mounted storage (Colab
Drive) or download the results archive regularly. SQLite state must be preserved
for resumption; the current CSV alone is not enough. Never have two notebooks
write to the same SQLite file. Kaggle output persistence depends on saving the
notebook version/output. Parallel sessions remain subject to provider quotas.

CSV fields include source video, file/checkpoint hashes, frame/time, OCR text,
detection class, confidence, bounding box, separate entity IDs, review status and
pipeline version. All generated rows are proposed; no verified-player database
is claimed. Source rights status remains unconfirmed. The cloud provider receives
the linked footage during processing. This pipeline does not bypass unavailable,
private or restricted videos; yt-dlp/cloud-IP download failures are surfaced.

The notebook is generated by `scripts/build_video_notebook.py`; rerun it after
worker changes. GPU inference, YouTube acquisition and the notebook cloud runtime
have not been exercised here. Local tests cover state, merge and entity semantics.
