# 05 — VOD Ingestion, Annotation and Evidence Pipeline

## Input tiers

1. `synthetic_json`: fixture-defined metadata and events; zero video rights risk; full automated tests.
2. `user_upload`: MP4/WebM in private storage (licensed/consented), manually annotated; first real MVP.
3. `cv_assisted`: optional local OpenCV/OCR/object detection proposes events, never auto-verified.
4. `official_approved_adapter`: Riot/GRID only after licenses, access scope, schema validation, legal review.

## Upload workflow and media handling

- UI obtains scoped upload grant after uploader confirms permitted usage and retention.
- `HEAD/POST assets`, chunked upload if needed; verify size/checksum/content-type and FFprobe duration. Server MUST reject executable masquerading as video; serve no direct public upload path.
- Assign playback timeline origin and compute proxy if needed using FFmpeg; asynchronous thumbnail generation. Annotate transcode errors with retry state.
- Source video remains immutable. Corrections create new annotation versions and invalidate dependent features.
- Match assignment is manually confirmed; neither OCR nor game client replay file automatically guarantees exact participants/rosters.

## Annotation editor

Left: video player with frame/time seek; center: sortable round event timeline; right: context inspector. Accessible keyboard controls: seek ±5 sec, add tag, mark start/end, assign human player, character pick, side, event and map region. Event requires evidence range, confidence, observed-vs-inferred distinction and context observation masks. Show 'needs review' queue and verification actions.

## Annotation tiers

- `draft`: user is marking possible event; not eligible for training.
- `proposed`: computer-assisted extraction; model-generated and unverified.
- `reviewed`: second analyst or authorized reviewer confirms event; eligible under quality policy.
- `rejected`: reason and timestamp retained in audit only.

Apply an explicit source-level exception for verified structured licensed telemetry; still log field-level provenance and data usage license.

## Quality assurance

- Random double annotation on ≥10% of pilot clips; measure Cohen's kappa for categorical labels and temporal tolerance for timecodes.
- Document event-specific annotation guidelines; avoid ambiguous labels such as 'aggressive' when an observable event could be tagged 'first-contact attempt'.
- Label conflict review dashboard and per-annotator agreement; make disagreements visible.
- Coverage metric per `map × side × round_phase × matchup/state × player × character_pick`.
- Validate frame seeking by absolute milliseconds; if source VOD has delay or editing, mark alignment as unreliable.

## Computer vision rollout strategy

**Phase CV0:** no CV requirement. Hand-label event/contexts accurately.

**Phase CV1:** detect HUD scoreboard, round boundary, UI element and abilities from owned recordings. Maintain patch-specific templates and manually review. Measure event detection precision/recall and time-alignment error.

**Phase CV2:** optional minimap localization with explicit calibration, visible frame and fog-of-war restrictions. Missing map visibility is a missing field, never 'enemy not there'. Benchmarks against independently labeled clips required.

**Phase CV3:** event proposal (ability deployment, plant, deaths). Never assert full 3D movement, precise teammate spacing, communication intent or all-ten-player paths without an authorized source that reliably includes them.

## Job DAG

`asset_received -> media_validated -> proxy_created -> round_annotation -> event_review -> feature_build -> style_rebuild -> coach_index_update`.

Each job has `(asset_id, pipeline_version, input_hash)` idempotency key; changes to version/hash retrigger downstream. Dead-letter failures after bounded retries. Processing only executes for active permission status. On withdrawal, cancel jobs and revoke signed URLs.

## Evidence object

Each insight cites event ID(s), source asset, `start_ms/end_ms`, match/round, annotation verification state, fields actually visible, supporting signal and permission gate. Clip `start`/`end` adjusts with player-specified buffer but never expands outside allowed asset. Cache URL expires quickly.

## Required QA fixtures

Create a 2-minute fake/synthetic video-free mock timeline, labeled events with conflicting observer annotations, missing HUD, edited VOD misalignment, source deleted mid-job, mixed rights, retry and duplicate upload. Tests must pass without GPU or network.
