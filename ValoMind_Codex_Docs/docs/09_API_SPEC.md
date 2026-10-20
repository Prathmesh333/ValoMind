# 09 — REST API Contract and Error Semantics

**Prefix** `/api/v1`; browser requests authenticated; all scope checks server-side. The companion OpenAPI seed lives at `spec/openapi.yaml` (not the full final contract; evolve alongside implementation).

## Endpoint inventory (proposed)

| Method | Path | Purpose | Min role |
|---|---|---|---|
| GET | `/health` | liveness/readiness separate deployment endpoints | public restricted |
| POST | `/organizations` | create private organization | user |
| GET | `/organizations/current` | current workspace and membership | viewer |
| GET/POST | `/players` | list/create permitted human-player profile | viewer/analyst |
| GET/PATCH | `/players/{id}` | authorized player metadata | viewer/analyst |
| POST | `/assets` | register owned/licensed upload + rights declaration | analyst |
| POST | `/assets/{id}/complete` | finalize bytes/hash/provenance | analyst |
| GET | `/assets/{id}` | private status and metadata | viewer |
| POST | `/assets/{id}/delete` | authorized deletion request | owner |
| GET/POST | `/matches` | list/create authorized matches | viewer/analyst |
| GET/POST | `/matches/{id}/rounds` | round timeline | viewer/analyst |
| GET/POST | `/rounds/{id}/annotations` | versioned labels | viewer/analyst |
| POST | `/annotations/{id}/review` | accept/reject with reviewer | coach |
| GET | `/players/{id}/profile` | versioned behavior summary | viewer |
| GET | `/style/categories` | versioned style taxonomy | viewer |
| GET | `/style/neighbors` | neighbors+support for player | viewer |
| POST | `/style/compare` | role-normalized and context comparisons | viewer |
| GET | `/compositions/{id}` | roster character-agent picks, versioned | viewer |
| POST | `/compositions/compare` | offline context-conditioned team analysis | coach |
| POST | `/coach/questions` | evidence-scoped coaching answer | coach |
| GET | `/evidence/{event_id}/clip` | temporary authorized clip access | viewer |
| GET | `/jobs/{id}` | progress/errors | analyst |
| GET | `/audit` | security/revisions history | owner |
| POST | `/me/export` | user data export request | user |
| POST | `/me/delete-request` | user deletion request | user |

## Canonical query filters

`map_id`, `patch_id`, `date_from`, `date_to`, `side=attack|defense`, `round_phase`, `character_agent_id`, `character_role`, `team_composition_id`, `review_status=reviewed`, `model_version`, `cursor`, `limit<=100`. Never treat filter omissions as permission expansion. Date/time UTC and ISO8601.

## Style compare request

```json
{
 "player_a_id":"p_a",
 "player_b_id":"p_b",
 "mode":"role_normalized",
 "filters":{"map_id":"ascent","side":"attack","patch_ids":["synthetic-1"]},
 "min_opportunities":20,
 "require_shared_context":true
}
```

`mode`: `role_normalized | context_matched | role_composition_breakdown`. If evidence insufficient return HTTP 200 with `status="insufficient_data"` and machine-readable warnings (rather than treating it as infrastructure failure); if unauthorized return 403/404 without leaking existence. Do not compute output simply based on agent role.

## Error format

Use RFC 9457-like `application/problem+json` with `type`, `title`, `status`, `detail`, `instance`, `code`, `request_id`, optionally `field_errors`. Stable codes: `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `CONSENT_REQUIRED`, `RIGHTS_UNVERIFIED`, `INVALID_EVENT`, `VIDEO_UNSUPPORTED`, `ASSET_LIMIT_EXCEEDED`, `JOB_CONFLICT`, `MODEL_UNAVAILABLE`, `RATE_LIMITED`.

## Request and response rules

- Content types JSON except signed upload and streamed media.
- All mutations support idempotency via `Idempotency-Key` when retryable.
- Limit strict cursor paging, server-side filter validation and capped date windows.
- Return `{data, meta:{request_id,model_version,schema_version,cursor,...}}` for collection reads.
- Include `source_evidence`, `synthetic`, `sample_count`, `coverage` and analysis version for derived behavioral responses.
- GET never triggers expensive recomputation synchronously; return last valid cached artifact or asynchronous job reference.
- All generated media/download URLs short-lived and permission-bound.

## API examples

Success insufficient-data:

```json
{"status":"not_comparable","distance":null,"coverage":{"shared_features":1,"possible_features":16},"warnings":["No overlapping attack-side contexts; compare same map/phase or collect more VODs"]}
```

Error:

```json
{"type":"https://valomind.example/problems/rights-unverified","title":"Rights not verified","status":403,"detail":"This asset cannot be published or analyzed under the requested purpose.","code":"RIGHTS_UNVERIFIED","request_id":"req_demo"}
```

## Versioning

Non-breaking additions within `/api/v1`; breaking fields require `/api/v2` or separate explicit schema version and migration. `event_schema_version`, `feature_recipe`, `style_model_version` carried on derived results. OpenAPI generated/validated in CI and typed TS client regenerated when routes change.
