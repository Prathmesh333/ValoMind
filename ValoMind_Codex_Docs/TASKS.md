# Executable Development Backlog

All `[ ]` unchecked: specifications and sample contracts are provided; implementation has **not** been performed. Each milestone is shippable and testable. Do not skip compliance gates.

## M0 — Foundation and engineering quality
- [ ] Initialize workspace with `apps/web`, `apps/api`, `workers/analysis`, `packages/ml`, `packages/contracts`.
- [ ] Provide lockfiles, `.env.example`, Docker Compose Postgres/Redis/object storage (or filesystem adapter), typed config, health checks.
- [ ] CI: Python Ruff+pytest; TypeScript lint/typecheck+Vitest; smoke Playwright; dependency and secret scans.
- [ ] Alembic initial migration corresponding to schema spec; fixtures isolated with `is_synthetic=true`.
- [ ] README: reproducible install, local seed, run, test, reset without cloud accounts.
- **Done:** fresh clone can start web/API/db and load synthetic match demo; CI green.

## M1 — Permissioned source ingestion and round annotation
- [ ] Private user/org/workspace role-based access, invite flow (or single-user local mock, with server-ready RBAC), audit log.
- [ ] Consent/license entity; upload source metadata with checksum/provenance and signed upload API.
- [ ] Async upload lifecycle `queued→processing→needs_review→ready/failed` with retries, progress and deduplication.
- [ ] Video timeline, round boundaries, player/agent assignment, manual annotation CRUD and edit history.
- [ ] Label validator, confidence/source, annotation verification by second reviewer, on-screen evidence links.
- [ ] Authz tests: cross-org file and label access denied; deleted source not accessible.
- **Done:** analyst uploads authorized video, labels five round moments, validates and replays selected timecodes; no unsupported extraction claims.

## M2 — Player profiles and cross-role playstyle categorization **(core differentiator)**
- [ ] Implement feature recipes in `docs/06`, including behavior rates conditioned on opportunity and situation.
- [ ] Track `agent_character`, official agent role, map, side, team composition as **context variables**, not primary player-style keys.
- [ ] Handle missing observation masks, low sample volume, patch drift, and overlap gating.
- [ ] Baseline player vector with robust scaler, player/match grouping, weighted distance, nearest-neighbor and HDBSCAN or agglomerative clusters with unassigned/noise option.
- [ ] Show cross-role similarity with conditioned feature contributions, examples of matched situations, uncertainty and evidence clips.
- [ ] Create editable human-readable taxonomy (e.g. proactive engager, patient space controller, reactive rotator) **only after feature evidence**, multi-label affinities.
- [ ] Report composition/role confounding and cluster stability, time-split and agent-held-out evaluations.
- **Done:** synthetic players A (Duelist) and B (Sentinel) with matched aggressive space-taking behavior are more similar than A and C (Duelist) with passive behavior; automated test proves this. Insufficient-overlap pairs get `not_comparable` rather than false 90% similarity.

## M3 — CoachAI evidence-grounded assistant
- [ ] Search validated events/clips with filters player, map, patch, game state and annotation provenance.
- [ ] Provide read-only tools: get_profile, compare_players, retrieve_events, get_round, get_cluster_explanation.
- [ ] Responses cite exact timestamps and distinguish observation from inference; abstain on empty evidence.
- [ ] Structured JSON report endpoint and prompt-injection-safe content retrieval.
- [ ] Eval suite: faithfulness/grounding, timestamp precision, unsupported-claim rate, expert usefulness.
- **Done:** coach asks for recurring rotation behavior, gets linked clips and correct limits; injection test cannot escape evidence constraints.

## M4 — Team lineup and composition-aware comparison
- [ ] Distinct schemas for 5 human players, their VALORANT character picks/roles, and AI model agents.
- [ ] Define side/map/patch/lineup representations; chemistry features, pairwise coordination, team-level styles.
- [ ] Provide compare-team-context API, with matched-situation controls; observational correlations never presented as causal.
- [ ] UI highlights when requested lineup lacks observations; multi-role flex player comparison works.
- **Done:** correctly compares style profile across two agent compositions without collapsing player identity to chosen character.

## M5 — Optional prediction and research simulation
- [ ] Establish action ontology and temporal supervised dataset from verified events, allowed signals only.
- [ ] Train simple interpretable baseline (logistic / boosted trees), probability calibration, time- and match-held-out evaluation.
- [ ] Add bounded offline counterfactual scenario explorer showing possible action distributions; no deterministic claim of intent.
- [ ] Only if supported: abstract multi-agent Monte Carlo world with transition model and synthetic/evaluated outcomes.
- **Done:** model card with accuracy vs baseline, log loss, ECE/Brier, coverage and abstention; never market simulation as actual game engine.

## M6 — Production readiness and team pilot
- [ ] Accessibility, responsive mobile read-only mode, job recoverability, quotas, retention/deletion and backups.
- [ ] Riot product registration/policy review, rights assessment, privacy terms, no logo misuse; feature-gated public launch.
- [ ] Coach trial with consented team, report workflow impact and user satisfaction.
- [ ] Record deployment playbook, incident response and rollback drills.
- **Done:** compliance approval gates documented; pilot repeatable with known costs and performance metrics.

## Example acceptance scenarios (must implement automated tests)

`S-01` Across-role twin proximity invariant; `S-02` no overlap => abstain; `S-03` removing agent identity features does not drop core accuracy below defined benchmark; `S-04` deleting player data removes derived embeddings and indexes; `S-05` hallucinated CoachAI claim rejected without evidence; `S-06` stale cluster version invalidates cache; `S-07` duplicate upload/job is idempotent; `S-08` tenant data never crosses permission boundary; `S-09` synthetic banner visible; `S-10` composition swap changes team-context insight but not immutable historical facts; `S-11` missing player positions remain null, never invented; `S-12` evidence clip links respect access controls.
