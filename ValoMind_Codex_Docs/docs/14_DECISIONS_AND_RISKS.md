# 14 — Decisions, Open Questions and Risk Register

## Architecture decisions

- **ADR-001:** offline/post-match only. Reason: game integrity, data availability, legal policy.
- **ADR-002:** manual reviewed labels first. Reason: VOD is not guaranteed complete telemetry; no invented movement data.
- **ADR-003:** modular monolith. Reason: simpler local development and testing.
- **ADR-004:** two-level representation: context-adjusted human player style + character/composition conditional behavior. Reason: role-agnostic similarity without deleting confounders.
- **ADR-005:** deterministic style metrics and structured analytics first; LLM for retrieval-driven explanation. Reason: calibrated numbers, audit trail and repeatability.
- **ADR-006:** match/time/player-aware evaluation and insufficient overlap abstention. Reason: protect against leakage and ungrounded cross-role inference.
- **ADR-007:** character composition distinct from AI software agents. Reason: domain clarity.
- **ADR-008:** synthetic/demo data labeled, never marketed as pro-player insights. Reason: accuracy and rights.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| No legally usable pro/third-party VOD telemetry | high | high | own and consented data, manual review, synthetic demos; explicit access gate |
| Role-agnostic clustering simply recovers character pick | high | high | conditional features, role leakage probe, swap invariance, coach blind review |
| Role or composition removes common situations | high | high | overlap thresholds, support-aware abstention, partial-pooling uncertainty |
| CV cannot track all 10 players from POV | high | high | missing data masks, restrict to observable annotations |
| LLM hallucinated psychological claims | high | high | event tools, claim verifier, absent-data abstention |
| Patches alter utility or map geometry | high | medium | patch-specific catalogs/models and drift monitors |
| Missing data unfairly penalizes low-sample roles | high | high | feature denominator and coverage fairness reports |
| Synchronized team analysis unreliable from one POV | high | high | no fabricated spacing; multi-POV permissioned source later |
| Unauthorized profiling/scouting concerns | medium/high | critical | scoped opt-in/private workflow, compliance gate, no pre-match workflow |
| Performance/cost exceeds budget | medium | medium | async jobs, sampling and local-first MVP |
| Demo perceived as actual player behavior | medium | high | synthetic labels, transparency docs, no real identifiers |

## Decisions needing real user/partner input later (not blockers for M0–M3)

- Confirm brand/trademark/domain and whether to call game character "agent" in marketing.
- Choose exact licensed footage or source for first non-synthetic pilot.
- Decide coach taxonomy labels with expert reviewers; keep cluster IDs stable and names editable.
- Decide jurisdiction-specific privacy/rights retention duration with legal review.
- Select production cloud/region and subscription only after compliance approval.
- Evaluate GRID access / Riot production key only if a permitted feature truly needs it.

## Explicit non-goals for MVP

No fully automated pro-player digital twins, no psychological certainty, no Riot replay binary exporter, no cheat-compatible overlay, no private opponent dossier, no guaranteed lineup win probability, no unsupervised analysis of unlicensed tournaments.
