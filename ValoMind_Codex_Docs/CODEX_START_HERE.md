# Codex: Read This First

You are the implementation agent for **ValoMind**, an offline, permission-based, VALORANT player-behavior analysis and coaching research platform. Treat this directory as the implementation contract. The goal is a working repository, not a UI mockup or generated ideas.

## Immediate execution instructions

1. Read `README.md`, `AGENTS.md`, `TASKS.md`, `docs/03_DATA_ACCESS_AND_COMPLIANCE.md`, and the PRD before writing code.
2. Inspect existing repository state; **do not overwrite pre-existing project work** without reason. If the repository is empty, bootstrap a monorepo with Next.js/TypeScript web, FastAPI/Python API, Python worker, Postgres with pgvector (optional at MVP), Redis, local MinIO (optional), Alembic migrations, pytest, Vitest and Playwright.
3. First finish milestone M0 and M1 from `TASKS.md`: development environment, synthetic fixtures, schema, authenticated private workspace, uploads metadata, and annotations; test these end-to-end.
4. Then M2 player profile and **role-independent style comparison**. Do not wait for a GPU, Riot production API, proprietary esports feeds, or externally sourced player footage. Use manual annotations and synthetic demo fixtures.
5. Produce migrations, API docs, typed clients, tests, README run commands, environment examples, and actual screenshots only when you can render the app. Never claim completed features based on stubs.
6. After each milestone, run tests and lints, record actual results and known blockers in a milestone report. Mark tasks complete only if acceptance tests pass.
7. If a decision is not specified, choose the smallest reversible implementation, document it in an ADR, and proceed. If a compliance-sensitive dependency is unknown, **disable that feature**, not the project.

## Mandatory domain behavior

The defining feature is that **two players may be categorized as stylistically similar even if one uses a Duelist agent and the other a Sentinel/Controller/Initiator agent**, provided sufficient comparable in-game situations exist. Implement role-normalized evidence and expose sample coverage, uncertainty, and within-role versus cross-role comparison diagnostics. Never simply cluster by agent picks, K/D, ACS, position labels or map composition.

Also model **the VALORANT agent lineup composition** (five characters selected by a team) as separate from **human player behavioral categories** and separate from **AI software agents**. Treat team synergy as a context-conditioned hypothesis requiring data, not an invented magical score.

## Implementation quality contract

- No real gameplay data unless explicitly permissioned. Demo must visually label synthetic data.
- No fake API success, fake trained models, fake calibrated percentages or invented pro-player profiles.
- Tests and schema validation included for every new endpoint and core pipeline.
- Schema migrations are reversible, idempotent jobs and deduplication included, errors typed.
- Python formatting Ruff, type checks where practical, TS strict mode, ESLint/Prettier, unit/integration/E2E pipelines.
- All secrets are environment variables. Tenant isolation, consent and deletion are requirements from day one.
- CoachAI must ground statements in validated events with footage timestamps; abstain when evidence insufficient.
- All external Riot/GRID connections are **interfaces disabled by default**, pending approval and valid credentials.
- No instructions for bypassing game protections.

## Report format at each completed milestone

`What shipped | files changed | migrations | commands run/results | API/UI demo path | security/privacy checks | known limitations | next tasks`

Start now with `TASKS.md` M0; do not generate the entire speculative product in one untested commit.
