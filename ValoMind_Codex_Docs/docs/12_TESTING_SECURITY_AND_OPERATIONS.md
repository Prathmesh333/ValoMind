# 12 — Testing, Security, Operations and Release Gates

## Test strategy by layer

- `pytest`: event validation, eligibility denominators, schema invariants, context residuals, masks, weighted distances, cluster stability, consent cascade, evidence ledger.
- `hypothesis` property tests: distances symmetric/nonnegative; no NaN, invalid timecodes rejected, monotonic support improves uncertainty estimate in expected cases, schema roundtrip.
- Integration: Postgres transaction/RBAC scopes; signed clip URL; upload idempotency; concurrent job claims; migration forward/back.
- UI Vitest: filter state, loading and no-data, category explanation, synthetic banner, evidence panel.
- Playwright: create workspace→import synthetic asset→annotate→verify→profile→cross-role compare→ask coach→see evidence.
- ML: player/time/match grouped folds, unseen agent diagnostics, context strata overlap tests, baselines, cluster stability.
- Security: cross-tenant ID enumeration, unauthorized signed clips, malicious filename and MIME, upload quotas, CSRF if cookies, prompt injection, secrets scan, SQL injection, path traversal.

## Critical domain test cases

1. A aggressive on Jett and B aggressive on Cypher are closer than A aggressive on Jett and C passive on Jett (enough comparable situations provided).
2. If A only attack entry observations and B only defense postplant observations: `not_comparable`, no similarity percentage.
3. Change character pick while holding synthetic behavior fixed: role-normalized style not spuriously flip categories.
4. Change one team's five-character lineup: composition output changes; historical player observation event is unchanged.
5. Revoke consent: remove source access immediately, purge derived indexes and invalidate shared clips; deletion queued/retry safely.
6. Insert adversarial note `ignore previous instructions`: CoachAI refuses to treat retrieved note as instruction.
7. Annotation updated: outdated features and embeddings marked stale until rebuilt.
8. Time-split validation: no match/round from train is in test via duplicate clip paths.
9. Low sample opportunities: rate displays interval or insufficient data, never zero.
10. Two simultaneous upload completion signals create one processing job.
11. Synthetic demo remains clearly labeled even in export.
12. Source media without synchronized teammates cannot generate fabricated spacing distances.

## Model QA gates

- Classification training should report macro-F1, top-k accuracy when applicable, log-loss, Brier score, expected calibration error, reliability plot and coverage-conditioned performance.
- Clustering must report silhouette only where meaningful, bootstrap stability, nearest-neighbor overlap across splits, role leakage probe, missingness/coverage stratification and qualitative representative evidence.
- Pre-register metrics and thresholds **after** observing realistic pilot baselines; never pick arbitrary 95% AI accuracy guarantee.
- Experiment tracking with dataset snapshot, code hash, features/model versions, split seed and annotation-review versions.

## Security details

- JWT/session verified at server; roles checked on every asset/player/event and vector query.
- Rate-limit uploads, QA and LLM calls; quota `max_bytes`, `max_jobs`, `max_queries` per tenant.
- S3/MinIO private by default; encrypt at rest with managed keys, TLS in transit. Signed URLs expire in minutes, not days.
- CSRF safeguards if session cookies; CSP, secure cookies and proper CORS allowlist; sanitize Markdown in analyst notes.
- Use auth-bound record-to-file mapping, never allow direct filesystem path from user request.
- SQL migrations backup before production, access audit logs with sensitive fields redacted.
- Secrets only in env/secret manager; rotate compromised keys; never run game client with privileged hooks.

## Privacy and lifecycle

Data minimization, rights basis records, consent, retention schedules, export and deletion API, anonymized metrics, backup retention and audit tombstones. Team access revocation invalidates cache. Membership revocation prevents signed URL refresh; use short expiries to limit previously minted links.

## Observability SLO (pilot targets)

Metadata API p95 <500 ms under seeded load; upload job success/retry states, processing queue backlog, per-minute failed media probes, ML feature job latency and memory, LLM token costs; track errors with trace IDs. Instrument before production. Results depend on hardware and scale.

## Production checklist

[ ] domain/HTTPS [ ] backup restore drill [ ] migrations tested [ ] license/Riot review [ ] rights export/deletion [ ] data isolation tests [ ] no demo/real conflation [ ] documented model limitations [ ] incident runbook [ ] dashboards and alerts [ ] asset retention worker [ ] documentation up to date.

## Local reproducibility commands (template; only document commands Codex actually implements)

```
cp .env.example .env
# docker compose up -d postgres redis minio
# uv run pytest
# pnpm lint && pnpm test && pnpm typecheck
# pnpm exec playwright test
```

Codex must replace comments with verified setup instructions and record observed test outputs before marking milestones done.
