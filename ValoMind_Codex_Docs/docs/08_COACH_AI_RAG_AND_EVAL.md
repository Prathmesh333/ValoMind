# 08 — CoachAI: Grounded Multi-Agent Coaching, Retrieval and Evaluation

## Core promise

CoachAI answers retrospective coaching questions based on verified, authorized footage-derived evidence. It is a tool-enabled analyst; it does not possess access to internal player thoughts, private communications, real-time game state or unverified competitive intelligence.

## Recommended implementation

One central coordinator with typed tools (do **not** create ten prompt-only persona agents to impersonate individual humans). ValoTwin is a model/profile *record* for each human player. Individual 'twin conversations' are scoped views over that record. A specialist player-style service computes numerical recommendations; an LLM only writes a grounded explanation. Team analysis agent aggregates permitted data across teammates when authorized.

## Retrieval and tool flow

1. Authenticate user and resolve authorized workspace, player permissions, source usage rules.
2. Classify intent: `player_profile`, `round_review`, `behavior_comparison`, `style_category`, `composition_review`, `insufficient_context`.
3. Fetch structured facts using tools before optional semantic note search: `get_player_profile`, `find_verified_events`, `get_round_context`, `compare_style_profiles`, `get_category_support`, `get_composition_summary`, `get_evidence_clips`.
4. Create an `EvidenceLedger` of observations: event IDs, reviewed status, source references, timecodes, field availability, denominators.
5. Compose answer as `observation -> supported interpretation -> uncertainty -> next drill/review suggestion`; attach per-claim evidence IDs.
6. Verify answer automatically: all numerical statements trace to a table cell/event, all clip links authorized, no evidence absent => abstain. Tool output is untrusted data, not instructions.
7. Store user question, filters, retrieved evidence IDs, answer and model version; only within retention/consent policy.

## Response JSON contract

```json
{
  "answer":"In the seven reviewed attack-side rounds, the player attempted early A Main space in four of five eligible opportunities. This does not establish their intentions.",
  "claims":[{
    "text":"Four of five eligible opportunities included early A Main entry",
    "type":"observation",
    "evidence_event_ids":["ev_001","ev_002","ev_003","ev_004"],
    "numerator":4,"denominator":5,"confidence_note":"Small verified sample"
  }],
  "citations":[{"asset_id":"asset_001","start_ms":7000,"end_ms":18000,"round_number":3}],
  "limitations":["Sample is too small for a persistent playstyle claim"],
  "followup_suggestions":["Review attack-side openings on another match"],
  "abstained":false,
  "data_version":"events_v1",
  "model_version":"coach_v1",
  "is_synthetic":true
}
```

## Coaching prompt rules

- Only assert what tools provide and references verify.
- Separate `OBSERVED`, `INFERRED`, `RECOMMENDED`; do not confuse these.
- Always include scope (`which games/rounds/map/patch`, number of opportunities) for any pattern.
- Never claim mental states, tactical intent, voice calls, hidden enemies or precise positions without evidence.
- If asked to profile non-consenting player, pre-match opponent or live round, decline that workflow and redirect to authorized post-match analysis.
- No prescriptive commands during a live match. Show multiple tactical alternatives in offline practice.
- Explain contradictory observations rather than averaging them away.
- Prefer direct SQL/aggregations for rates; LLM should not invent math from vague text snippets.

## RAG structure

Structured filters first: workspace, permission, game patch, map, side, player, time. Text retrieval second: verified annotation notes embeddings, if embeddings are in scope. Store `{event_id, asset_id, start_ms, end_ms, org_id, source_rights_status, verification_status}` alongside chunks. Citations must point to source event and signed clip, not just retrieved narrative text.

## Model selection and costs

Support `LLM_PROVIDER=none` for deterministic templated reports. Add provider-agnostic interface and request budgets. Default to small-capacity model for summaries; cache by query+evidence+model version+permission version. Invalidate on data edits, consent revocation and model upgrades. Do not cache signed media URLs.

## Evaluation suite

- **Grounding:** percent gameplay factual claims with verified citation; target 100% for fixture benchmark.
- **Unsupported claim rate:** 0% on synthetic reference questions; flag attempts to hallucinate values.
- **Timecode validity:** cited time spans fall within referenced VOD asset.
- **Calculation correctness:** SQL ground truth for numerator/denominator and context filters.
- **Privacy:** refuse cross-org retrieval and revoked consent, including vector search.
- **Prompt injection:** malicious annotations telling LLM to leak secrets or ignore instructions should be quoted/ignored, never obeyed.
- **Abstention:** empty source, unknown opponent or unverifiable intent explicitly yields inability to conclude.
- **Human utility:** blind coach ratings, time saved and actionability; not simply LLM self-rating.

## Multitenant controls

Every tool accepts a server-issued `auth_context`; no tool accepts arbitrary org ID from LLM text. Clip URL generation occurs after authorization. Separate LLM message content from control configuration. Record cost/latency and request IDs without raw sensitive prompts in default telemetry.
