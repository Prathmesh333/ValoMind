# Implementation status — 2026-10-20

M0 remains incomplete. No later milestone is marked complete.

Repository published to Prathmesh333/ValoMind on main. GitHub CI run 39404925597
passed lint, formatting, all 64 tests and PostgreSQL upgrade/downgrade/re-upgrade.
An initial Actions health-command quoting issue was fixed before that successful
run. Local Docker remains unavailable; earlier notes about unobserved CI below
describe the state when those increments were written. Footage, generated results,
weights and local environment files are excluded from Git.

video_v5: strong spatial compound HUD admission, preserved weak-signal confirmation
and replay/break precedence; source-scoped IQOT team alias. Saved-text replay now
admits 55/60 samples, and existing OCR reparses to 320/320 team-bearing roster rows.
These are diagnostic results, not new cloud inference or independent accuracy.
See FILTER_V5_FIXES.md. No model training or database migration.

video_v4 increment: targeted crop OCR retry, optional abstaining portrait reference/
learned-classifier adapters, independently reviewed/source-separated classifier
dataset builder, segment sample images and evaluation tooling. The ten-image
cross-layout reference experiment abstained on all queries, so no recognition
accuracy or trained model is claimed. Cloud OCR retry and independent-broadcast
validation remain pending. See EXTRACTION_IMPROVEMENTS.md. No DB migration.

Roster increment: spatial parsing for inspected VCT buy/sidebar layouts, scoped
handle/team aliases, current-map extraction and evidence-linked roster CSVs.
Actual second-run OCR yields 319 roster proposals (274 with team, 45 unknown),
covering ten displayed handles on Split. Optional cloud portrait crops and a local
20-image review pack prepare character classification; agent IDs remain blank.
No model training, global identity resolution or full match segmentation claimed.
Details and validation are recorded in ROSTER_EXTRACTION.md. No migration.

Broadcast filter increment: video_v2 adds an upper-HUD OCR rules filter before
full-frame extraction. Consecutive gameplay/roster signals admit extraction;
detected fillers/replays skip it; uncertainty produces review entries. Per-sample
segments.csv contains reasons, probe text and resumable transition state.
Default notebook settings enable filtering. Unit/integration tests use synthetic
OCR/decoder doubles; no real broadcast precision/recall or GPU benchmark exists.
Unmarked replays and unfamiliar layouts remain limitations. No database migration.

Cloud video increment: standalone Colab/Kaggle notebook supports bounded YouTube
channel listing, video URL acquisition in the cloud, sampled EasyOCR proposals,
optional custom YOLO weights/training, labeling-frame export, separate entity
aliases, per-job SQLite resume and deduplicated CSV merge. See notebooks/README.md.
No real video download, GPU training or cloud execution has been verified here.
Player-agent-team relationships and match/map segmentation are not automatically
resolved; OCR/detector output remains proposed. No migration or new API route.

Broadcast indexing increment: added a strict local manifest, reviewed player/team/
map-agent observation export, synthetic cross-map fixture and CLI. See
BROADCAST_INDEX.md for commands and limits. No schema migration or external footage
integration was added. Unknown values remain null; model proposals stay outside
the reviewed index. This is metadata infrastructure, not working OCR or YOLO.

Shipped: API liveness/readiness, token-protected synthetic JSON demo, problem JSON
errors and request IDs; Python dependency lock; initial Alembic migration with
composite tenant foreign keys for source consent and consent subjects; PostgreSQL
and Redis Compose configuration; generated OpenAPI; local run instructions; video
training plan. Frontend, worker and ML folders explicitly describe pending work.

Files: apps/api (service, configuration, tests and migrations), infra/compose.yaml,
pyproject.toml, uv.lock, scripts/export_openapi.py, packages/contracts/openapi.json,
.github/workflows/checks.yml, .env.example, README.md and docs/.

Migration: 0001 snapshots the representative schema from the supplied spec. It is
an initial foundation, not the complete future entity model. Application-level
event time/round/match consistency and tenant RBAC await M1. No private CRUD routes
exist yet. PostgreSQL extension pgcrypto is retained on downgrade.

Validation: uv sync; Ruff check and formatting; pytest; Alembic upgrade and downgrade
SQL generation; OpenAPI export. The final test counts are recorded by the completion
message. PostgreSQL apply/reverse/reapply is configured in CI but has not run here:
Docker is unavailable. The HTTP test client emits an upstream Starlette deprecation
warning about httpx; tests pass. No CI-green or end-to-end UI claim is made.

Demo path: /api/v1/demo/match with configured bearer token. This reads invented
fixtures, does not seed the database, process footage or train a model. Swagger UI
is available at /docs. No screenshot is provided because no product UI exists yet.

Privacy: no real footage, secrets, accounts or third-party identities ingested;
empty token disables fixture access; invalid tokens are rejected; no external
integration exists. This demo token is not a substitute for M1 member authentication.

Next: finish M0 web application and typed client, fixture seed, frontend tests,
dependency/secret scans and a real PostgreSQL verification run. Then M1 workspace
RBAC, permissioned upload, durable jobs, annotation editor and independent review.
Only then collect the pilot dataset described in VIDEO_MODEL_PLAN.md.
