# ValoMind Repository Instructions for Codex and Other Coding Agents

## Context and non-negotiables

ValoMind is a post-match, consent-based coaching product. Cross-role playstyle similarity is the differentiator. Functional requirements live in the docs; acceptance and sequencing in TASKS.md. Riot policy compliance always overrides a requested implementation detail. No live competitive assistance or pre-match opponent profiling.

## Working practice

- At start of every feature: identify document requirement IDs, affected data boundaries, input permissions, data coverage assumptions and tests.
- Submit small coherent milestone increments; never mark a UI implemented unless backed by API or clearly labeled fixture/demo mode.
- User-facing defaults should be transparent and conservative: empty, insufficient-data, approximate, error and synthetic states must be visible.
- Distinguish facts observed in footage, manually annotated labels, model estimates and model-generated explanations.
- Make asynchronous video jobs resumable/retryable and safe against duplicate processing.
- Retain original input source metadata and label provenance so every behavioral statement is auditable.
- Use alembic migrations, Postgres constraints, Pydantic request validation, OpenAPI docs and typed frontend fetch client.
- No hardcoded user accounts, external keys or backend secrets.
- Prefer boring, testable modules over a distributed swarm. Ray is optional until processing volume justifies it.

## Suggested code layout

```text
apps/web/                     # Next.js App Router, typed components/routes
apps/api/                     # FastAPI routers, auth, service layer, migrations
workers/analysis/             # job handlers and offline VOD processing
packages/contracts/           # JSON Schema/OpenAPI types, shared fixtures
packages/ml/                  # feature engineering, clustering, evaluations
infra/                        # compose, config, migration scripts
scripts/                      # seed-synthetic, healthcheck, validation
examples/                     # exclusively rights-cleared demo media
```

## Branch and commit convention

`feat/m0-bootstrap`, `feat/m1-annotations`, `feat/m2-style`, ...; write small commits with tests. Record decisions under `docs/adr/ADR-NNN-...md` when changing defaults. Do not wipe uncommitted work.

## API conventions

`/api/v1/` prefix; UTC timestamps in ISO 8601; UUID IDs; `application/problem+json` standardized errors; cursor paging; every list scoped to organization/workspace with RBAC. Clients never submit their own org ID as authority without server membership validation. File uploads via signed URLs or local dev gateway with allowlisted MIME and size quotas.

## ML conventions

Version every input schema, label schema, feature recipe, map patch, model, scaler and cluster assignment. Split by match/time/player to prevent leakage. Report support and uncertainty. Start with transparent handcrafted/annotated features and unsupervised clustering, not automatically hallucinated psychological labels. Human analysts can review/rename clusters.

## Safety / compliance checks before shipping

[ ] offline only  [ ] rights and consent records  [ ] no current opponent scouting  [ ] no real-time overlay  [ ] tenant access isolation  [ ] deletion cascade  [ ] evidence grounding  [ ] synthetic demo labeling  [ ] Riot registration/approval check for public launch

## Stop conditions

Block external data integrations pending authorization; block public sharing of unconsented player records; block behavioral predictions that expose identity of hidden users; block release of claims labeled as observed without verified source events. Continue on synthetic/consented fixture paths instead.
