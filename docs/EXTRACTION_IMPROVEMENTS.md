# Extraction improvements — video_v4

Added targeted OCR retries before roster parsing. Only unresolved team/name regions
are retried; missing name slots require an already established layout. Crops are
enlarged 3x and OCR boxes are translated back into source coordinates. Original
results remain present; retries are labeled retry.team or retry.player_name. The
existing admission thresholds and conflicting-identity abstention are unchanged.
This targets the observed Jamppi miss and unclear scoreboard text without assigning
identities from adjacent frames. New identity/version settings create a fresh job.

Added optional portrait enrichment in roster_with_agents.csv. Two implementations:
a diagnostic grayscale reference matcher, and an adapter for a trained YOLO image
classifier. Both have minimum-score/margin gates, preserve unknown results, and
leave review_status=proposed. Model versions/checkpoint hashes are exported.
HUD detection weights and portrait classification weights are separate settings.
Generic ImageNet classification weights are rejected for agent extraction; class
names must match the configured character catalog, with unknown/occluded classes
mapped to abstention. Thresholds are pilot defaults, not validated calibration.

Actual reference experiment: ten buy-phase portraits as references versus ten
sidebar portraits from the same footage. All ten queries abstained at the default
thresholds. This demonstrates that simple template features are not currently a
useful cross-layout character classifier; no 100% self-match result is reported as
accuracy. Inputs use assistant-proposed labels and are not independent validation.
Saved diagnostic scores in results/portrait_diagnostic/cross_layout.csv. Leave
reference matching disabled for production and use the learned-model path after
collecting and independently reviewing a sufficiently varied dataset.

prepare_portrait_dataset.py builds train/val/character folders only from independently
reviewed labels. It requires source-separated split assignments, matching class
coverage and no identical images crossing splits. It rejects existing output
folders and source-path escapes. The 20-image pack currently fails eligibility;
its labels remain proposals and there is no separate validation video. No data
was silently promoted or neural classifier trained. The notebook includes an
optional yolo11n-cls training cell on GPU 0 with AMP and batch 16. Classification
uses a directory dataset rather than a detection YAML, as documented by
[Ultralytics](https://docs.ultralytics.com/tasks/classify/).

The notebook saves one JPEG every fifth sampled frame, capped at 24 per job by
default, across all segment states. segment_review_suggestions.csv links images
and proposed decisions. Copy it to segment_review_labels.csv, fill reference_segment,
review_status=reviewed and reviewer_id, then run evaluate_segment_review.py. The
evaluation reports confusion counts, missed gameplay/roster samples and admitted
fillers/replays. Suggestions are regenerated; reviewed labels use a separate file.
Sampling is systematic and bounded, not an exhaustive full-video benchmark.

Validation: unit/integration tests cover missing-field retries, coordinate translation,
one low-confidence name recovered after retry, portrait abstention and GPU adapter,
source split leakage, label eligibility and reviewed segment evaluation. A new cloud
preview is needed to measure real OCR recovery; no actual T4 retry run has happened
here. Independent broadcast accuracy and neural training remain pending data, not
claimed as completed improvements.

Commands:

```powershell
uv run python scripts/prepare_portrait_dataset.py path/to/reviewed.csv path/to/new_dataset
uv run python scripts/evaluate_segment_review.py path/to/segment_review_labels.csv
```

In Colab, run the rebuilt notebook with CROP_OCR_RETRY=True. Leave portrait model
paths empty until you have reviewed references or trained classification weights.
Collect the new roster CSV and segment review images before considering a full-hour run.
