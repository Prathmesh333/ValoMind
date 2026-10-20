# 11 — Implementation Order, Work Packages and Dependencies

## Why this order

Data rights and evidence integrity precede ML. Manual labeling precedes speculative computer vision. Role-independent similarity is useful without full match telemetry. Team simulation is optional research only after predictive model validation. Milestone numbering matches `TASKS.md`.

| Milestone | Estimate (planning only) | Inputs | Output/demo | Main risks |
|---|---|---|---|---|
| M0 foundation | 1 week | none | stack running, synthetic fixtures, CI | dependency drift |
| M1 ingestion/annotation | 2–4 weeks | M0, rights-cleared VOD | upload→label→review→clip | VOD timestamp quality |
| M2 cross-role StyleMap | 2–4 weeks | reviewed events, enough opportunities | neighbors and explanatory categories | sample overlap / confounding |
| M3 CoachAI | 1–3 weeks | M1/M2 | citations and abstention | LLM hallucination |
| M4 compositions | 2–4 weeks | lineups and team observations | context-aware team reports | sparse lineups |
| M5 prediction/simulation | research time, open-ended | curated sequential data and validation | bounded action distribution | calibration, validity |
| M6 pilot/launch | depends on legal and partners | all, approvals | repeatable partner pilot | rights and policy |

Estimates are rough and not commitments. Codex should optimize for verifiable tests and working vertical slices rather than shipping everything at once.

## Implementation sequence for a solo developer

1. Docker Compose + Python/Next.js scaffolds, seeded synthetic match and annotation fixtures, schema migration, typed models.
2. Basic org/workspace authorization, source rights flags and upload status page.
3. Asset upload + private playback and event/round annotation UI.
4. Feature engine with context denominators and missing masks; tests on synthetic players.
5. Similarity service and cross-role category view; coverage gates and explanation cards.
6. CoachAI tools with deterministic template baseline and clip citations; LLM optional provider integration.
7. Composition metrics and compare page, without claiming win-rate uplift.
8. Only later automate UI event extraction, predictive action modeling and advanced embeddings.

## Work package acceptance template

Every PR contains: `requirement IDs`, `schema/API changes`, `test cases`, `demo instructions`, `data privacy implication`, `feature flags`, `known limitations`. All new code must be validated by a green test suite, not just compile.

## Suggested repository GitHub issues (one per slice)

`[M0] bootstrap monorepo`, `[M0] migrations and health checks`, `[M0] fixture generator`, `[M1] permissions and rights declarations`, `[M1] media upload`, `[M1] annotation round editor`, `[M1] review API`, `[M2] contextual feature calculator`, `[M2] role-normalized distance`, `[M2] clustering + stability`, `[M2] compare UI`, `[M3] evidence ledger and CoachAI`, `[M4] lineup composition module`, `[M5] calibrated classifier`, `[M6] data deletion, retention and release gates`.

## Hard launch/scale gates

**Gate A** basic upload, review and player profile works without official game API. **Gate B** clustering survives agent-role swap synthetic test, reports missing data, and passes coach blind review. **Gate C** CoachAI answers are evidence-backed. **Gate D** Riot/rights approval appropriate to public/team feature is received. **Gate E** model calibration and measured value justify simulation marketing. Failing any gate must not silently be bypassed.
