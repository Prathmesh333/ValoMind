# POV evidence and frozen visual features

This increment supports PRD-03 (reviewed event annotation), PRD-04 (support and
uncertainty), PRD-07 (grounded explanations), and the M1/M2 evidence boundary in
the original specification. It does not complete those milestones. All processing
is offline. The existing source rights status remains unconfirmed until recorded.

## Native frame evidence

The notebook now proposes at most six four-second review windows from sampled
gameplay decisions per job. These are coverage samples, not action detections,
and the segment filter is still fallible. Change `windows` to select an engagement.
Disable `EXTRACT_POV_WINDOWS` to skip the additional decoding/storage cost.

PyAV seeks and decodes the original presentation timestamps (PTS); no frame-rate
conversion is performed. Each window has source SHA256, PyAV version, original
PTS/time base, source-relative millisecond timestamps and saved frame IDs in
`pov_review/<window_id>/frames.csv`. Completed windows resume without re-decoding.
There is an eight-second/1000-frame limit per window and 20-window limit per call.
JPEGs can be large; the default is up to 24 seconds of native frames per job.

Copy `pov_events_to_review.csv` to a new CSV and annotate each event. The template
is never overwritten. For additional windows on a later run, create extra rows
using the new frame manifest's window ID. Required fields are:

- Unique `event_id`, `window_id`, known `player_id`; retain team/map/round context
  when verified. Do not infer player identity from the previously observed camera.
- `cue_type=enemy_first_visible`; `action_type=shot`, `ability`, or `disengage`.
- `cue_frame_id` and `action_frame_id` referencing actual saved evidence frames.
  Inspect preceding frames to bracket the first visible cue and first action.
- `review_status=reviewed`, `reviewer_id`, `perspective=player_pov`, and explicit
  `true` for `player_identity_verified`, `xray_absent`, `continuous_view`, and
  `cue_visibility_verified`. An authorized reviewer must check these; setting
  flags does not itself prove visibility. Retain `earlier_cues_unknown=true` when
  earlier audio/information cannot be established.

Set `REVIEWED_POV_EVENTS` to the annotated CSV and rerun the evidence cell.
`response_windows.csv` contains the video estimate, temporal sampling bounds,
review provenance and exclusion reasons. Cuts, replays, X-ray, unknown identity,
missing evidence and an unbracketed onset produce no numeric latency. A broadcast
first-person view is not automatically a faithful record of the player's screen.
Review must exclude known replay/observer discontinuities before marking player POV.

The metric is **visible cue-to-action latency**, not physiological reaction time.
For observed cue time C and action time A, point estimate is A-C. With preceding
timestamps Cprev and Aprev, sampling bounds are max(0,Aprev-C) to A-Cprev. These
bounds do not include observer, network, audio, display or input delay. Shot/ability
detectors, calibrated crosshair measurements, tactical context extraction and
coordination metrics are not yet implemented. No thoughts, emotions or personality
labels are generated, including from facecams.

## Optional ViT features on one GPU

`RUN_VIT=False` by default. Enabling it installs optional Transformers dependencies
and loads frozen `facebook/dinov2-small` on `cuda:0`, batch size four, inference
mode and FP16 autocast. It records the immutable Hugging Face checkpoint commit
in every row. This is a starting configuration for a free T4, not a benchmark or
guarantee of memory availability. OCR/YOLO processing finishes before this stage;
the encoder is released afterwards.

Create `VIT_SAMPLES_CSV` with columns:

```text
sample_id,image_path,x1,y1,x2,y2,crop_kind,crop_review_status,reviewer_id,source_sha256,timestamp_ms
```

Coordinates are pixels in the saved image, and relative image paths resolve
against the sample CSV. Only reviewed `gameplay` or `character_portrait` crops
are accepted. A reviewer must exclude facecams, audience/caster faces and other
non-gameplay regions; this module does not automatically detect those regions.
Keep player/map/round/source IDs as additional columns when known.

Outputs are `visual_features.jsonl` (normalized, **unlabeled** vectors plus source,
crop hash, checkpoint and review metadata) and `visual_features.review_queue.csv`
(at most 100 diverse samples, chosen by farthest-first cosine distance). Diversity
is neither confidence nor semantic importance. Embeddings are not event labels.

DINOv2 is a ViT feature extractor: [official documentation](https://huggingface.co/docs/transformers/model_doc/dinov2).
Use it to collect visual representations, retrieve similar samples and select
labels for review. A temporal model such as [VideoMAE](https://huggingface.co/docs/transformers/model_doc/videomae)
is a later candidate for clip classification once reviewed event labels exist.
Neither architecture inherently knows VALORANT actions or improves this dataset
without evaluation. Keep YOLO for bounding boxes and OCR for text. Supervised
training on reviewed teacher boxes is pseudo-labeling; transferring ViT weights
directly into YOLO is not implemented and is not generally compatible.

Evaluate any trained classifier against the existing baseline on unseen complete
matches, with temporal event tolerance and unknown/abstention coverage. Never split
neighboring frames or overlapping windows across training and validation. Review
at least 10% of pilot clips twice to measure categorical agreement and timing
disagreement before using timing distributions in player comparisons.
