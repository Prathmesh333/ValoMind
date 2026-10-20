# ValoMind — AI Player Intelligence and Coaching

**Status:** engineering specification / staged implementation blueprint, not a claim that an implementation already exists.  
**Version:** 1.0 · **Date:** 2026-10-20 · **Primary implementation assistant:** Codex.

> **Mission:** Turn authorized, offline VALORANT match footage and structured annotations into evidence-backed player behavioral profiles, role-independent playstyle groups, team-composition insights, and coach-facing answers. A later research phase evaluates player-action prediction and bounded scenario modeling.

## How to hand this project to Codex

1. Give Codex this whole folder (or the downloadable ZIP) in a repository or workspace.
2. Start with `CODEX_START_HERE.md`, then `AGENTS.md`, `TASKS.md`, and `docs/01_PRODUCT_PRD.md`.
3. Tell Codex: **"Implement ValoMind iteratively following AGENTS.md and TASKS.md. Start at M0, use mock/synthetic demo assets without external permissions, make each vertical slice executable and tested, and do not silently skip acceptance criteria. Produce code, docs, tests, migration, and run instructions."**
4. Do not supply Riot keys, private VODs or other secrets in prompts; inject secrets through environment configuration once explicitly authorized.

## Documents

| File | Purpose |
|---|---|
| `CODEX_START_HERE.md` | First Codex prompt, sequencing, definitions of done |
| `AGENTS.md` | Mandatory engineering behavior and guardrails for agentic coding |
| `TASKS.md` | Trackable implementation backlog and milestones |
| `docs/01_PRODUCT_PRD.md` | Personas, goals, workflows, acceptance requirements |
| `docs/02_SYSTEM_ARCHITECTURE.md` | Services, boundaries, deployment and observability |
| `docs/03_DATA_ACCESS_AND_COMPLIANCE.md` | Riot policy, provenance, permissions and prohibited features |
| `docs/04_DATA_MODEL_AND_EVENT_SCHEMA.md` | Canonical event taxonomy, data types, validation, storage |
| `docs/05_VOD_ANNOTATION_PIPELINE.md` | Ingestion, timestamps, labeling, QA and computer vision rollout |
| `docs/06_PLAYER_TWIN_AND_STYLE_CLUSTERING.md` | Cross-role player categories, debiasing, embeddings, comparisons |
| `docs/07_TEAM_COMPOSITION_AND_SIMULATION.md` | Agent picks, team chemistry and safe research simulations |
| `docs/08_COACH_AI_RAG_AND_EVAL.md` | Retrieval, tools, answer evidence, AI evaluation |
| `docs/09_API_SPEC.md` | Endpoint behaviors, pagination, errors, authorization |
| `docs/10_FRONTEND_UX.md` | Routes, UI states, interaction and accessibility |
| `docs/11_IMPLEMENTATION_ROADMAP.md` | Dependency ordered engineering phases |
| `docs/12_TESTING_SECURITY_AND_OPERATIONS.md` | Security, QA, performance, production readiness |
| `docs/13_PITCH_AND_RESEARCH.md` | Portfolio demo, coaching research and validation |
| `docs/14_DECISIONS_AND_RISKS.md` | Architectural decisions, open dependencies and mitigations |
| `docs/15_GLOSSARY.md` | Domain vocabulary to avoid category ambiguity |
| `spec/openapi.yaml` | API contract draft; expand while implementing |
| `spec/schema.sql` | Starter PostgreSQL schema; evolve with migrations |
| `fixtures/` | **Synthetic** examples for tests/demo only |

## First achievable demonstration

An analyst creates a private workspace, uploads authorized footage, labels five rounds, reviews validated events, generates a player profile, inspects **role-agnostic similarity** between two players on different VALORANT agent picks, and asks CoachAI a question answered with source clips and confidence limitations.

## Hard boundaries

- **Offline after-match analysis only**; no gameplay overlay, cheat, memory reading, packet sniffing, client hooks, or current-opponent pre-match scouting.
- Do not equate VALORANT **agents** (playable characters) with ValoMind **AI agents** (software reasoning/model components).
- Do not claim footage reveals intent or private team communications; infer only observable behavior and explicitly state uncertainties.
- All player-specific shared data needs appropriate permissions/opt-in and access control; obtain necessary Riot approval before launching a public product. See compliance doc.
- Features requiring unavailable telemetry or rights must stay feature-flagged or synthetic until authorized.

## Source-of-truth order

Policy and legal constraints > real licensed data availability > specification > code assumptions. Where docs conflict, record an ADR and fix the docs. All sample measurements in fixtures are invented and must never be portrayed as real observations.
