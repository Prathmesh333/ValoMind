# 04 — Canonical Data Model and Event Schema

## Modeling principles

Human player identity, selected VALORANT character, character **role**, in-match team, 5-character **composition**, and AI software agent are different entities. All observational records must point to a real authorized source and preferably a timestamp. Missing fields are `null` with reason, not guessed defaults.

## Entity list (tables)

- `users`: login identity (can be delegated to auth provider), email hash/preferred name.
- `organizations`, `memberships`: tenant and role (`owner`, `coach`, `analyst`, `viewer`).
- `consents`: player/uploader rights and allowed uses, expires/revokes.
- `assets`: private footage metadata, checksum, rights, consent state and lifecycle.
- `players`: tenant-owned human profiles and pseudonyms; `external_puuid` optional encrypted/protected.
- `maps`, `patches`, `character_agents`: versioned reference catalog; class role is a characteristic of character, **not a proxy for player style**.
- `matches`: patch, mode, map, start time, footage source, synthetic flag, permission scope.
- `match_players`: relationship of human player and in-game character pick, team, side if applicable, starting/ending roster changes.
- `rounds`: match, number, time interval, attack/defense, winner (if verified), score/economy observations.
- `annotations`: human or CV suggested observation, reviewer, timestamps, version, reason, confidence.
- `events`: canonical, validated behavioral event: `player`, `round`, timecode, event type, game context, observed properties, provenance and verification.
- `contexts`: optional state snapshots linked to events; availability masks for visible information, known/unknown enemies, team economy, spike state, numerical advantage.
- `clips`: time-bounded references into source footage with asset ACL.
- `feature_sets`: player time window+cohort+recipe+coverage JSON, context strata, feature vector/mask and version.
- `style_models`: clustering procedure, feature recipe, training data fingerprint, hyperparameters, taxonomy and validation report.
- `style_assignments`: player→cluster IDs, multi-label membership, support, uncertainty, version.
- `pairwise_comparisons`: player A/B, query context, calibrated (if applicable) similarity, breakdown, overlap and status.
- `team_compositions`: match/team/round subset, ordered five character IDs, composition features and patch.
- `coach_queries`, `coach_answers`, `evidence_links`: scoped conversation, actual retrieved event/clip citations, abstention reason, model version.
- `jobs`, `audit_log`: lifecycle, lineage, idempotency, access/deletion audit.

## Event taxonomy v1

| Type | Explicit observed event examples | Denominator for rates |
|---|---|---|
| `movement.route_segment` | segment entering A lobby at t1–t2 | observed path opportunities |
| `engagement.peek` | swings corner at t (visibility dependent) | eligible corner encounters |
| `engagement.first_contact` | player involved in first verified duel | eligible opening opportunities |
| `engagement.disengage` | repositions after first contact | confirmed contact opportunities |
| `space.enter_site` | first approach into site area | verified execute opportunities |
| `utility.deploy` | observed ability deployed at time | known accessible utility opportunities |
| `team.trade_attempt` | teammate attempts follow-up duel | observed tradable teammate deaths |
| `team.spacing` | pairwise displacement/time at observed keyframe | observed synchronized pair states |
| `rotation.commit` | sustained path from one objective to other | documented rotation opportunities |
| `decision.save_or_retake` | observable attempt to save / retake | late-round opportunities verified |
| `objective.spike_interaction` | plant, tap, defuse or carry | known spike states |
| `economy.purchase` | verified buy choices in buy phase | observed purchase rounds |

**Inference versus fact:** `intent`, `communication_quality`, `mental_state`, `panic`, `tilt` are **not** directly observable event types. If an analyst uses such words, label them as an interpretation in a separate free-text commentary field, not ground-truth facts.

## Canonical event JSON contract example

```json
{
  "schema_version": "1.0",
  "event_id": "8f8b7d03-2830-4879-b431-9d4c3f9d4441",
  "organization_id": "b1da9bdf-96de-4ef8-8b8d-7a7a7bb5f861",
  "match_id": "7e87bf1e-8a24-42bf-8594-980a8fbb6394",
  "round_number": 7,
  "player_id": "a6c7cb4b-34ee-47d0-958d-356305aa7cef",
  "character_agent_id": "jett",
  "observed_at_ms": 104920,
  "event_type": "engagement.peek",
  "location": {"map_region": "A Main", "x": null, "y": null, "coordinate_system": "unavailable"},
  "context": {"side":"attack", "phase":"mid_round", "team_alive":4, "enemy_alive":null, "spike_state":"unknown", "composition_id":"comp-demo-1"},
  "properties": {"peek_type":"wide", "outcome":"disengaged", "vision_limited":true},
  "source": {"asset_id":"7e104ed1-6311-4e64-a8b5-08b25af8fe43", "start_ms":103100, "end_ms":106200, "annotation_id":"a-demo-1", "extraction_method":"manual", "verified":true},
  "quality": {"confidence":0.86,"visibility":"partial","missing_fields":["enemy_alive","location.x","location.y"]},
  "is_synthetic": true
}
```

## Validation rules

- All timecodes nonnegative and within asset duration; `clip_start_ms <= observed_at_ms <= clip_end_ms` where applicable.
- Events never reference another tenant; confirmed match and player IDs must resolve.
- An optional coordinate requires a named coordinate system and map calibration/version; do not infer game world coordinates from arbitrary video pixels.
- Each event has `schema_version`, origin and verification. Only `verified=true` is eligible for model training by default.
- Event revision creates audit metadata and invalidates dependent feature outputs.
- Round numbering unique per match; `round_start_ms < round_end_ms`; timecode origin stored per asset (whole VOD or round-local).
- `composition_id` may be missing if picks unknown; unknown is not equal to no composition.
- No record considered verified simply because model confidence > threshold; requires independent trusted source or authorized reviewer.

## Lineage / invalidation

A source deletion or permission revocation traverses sources→annotations→events→clips→feature sets→style assignments→retrieval indexes→coach answers caches. Preserve only lawful minimum audit tombstones stripped of gameplay content.

## Physical DB starting point

See `spec/schema.sql` for representative indexes, constraints and core tables. Implementation uses Alembic migrations and adds tables as milestones mature. Do not run sample SQL unreviewed on a production database.
