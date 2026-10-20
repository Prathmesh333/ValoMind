# 03 — Data Access, Rights, Privacy and Riot Compliance

**As-of verification:** 2026-10-20. This is an engineering compliance checklist, not legal advice. Recheck all policies before release; policy change may invalidate parts of this plan.

## What is and isn't available

- Riot's public VALORANT developer documentation enumerates content, match/match-list, leaderboard and status APIs. **Do not assume these APIs expose unrestricted tick-by-tick positions, synchronized ten-player video streams, arbitrary pro-player stats, comms, or replay binary parsing.** See official docs: https://developer.riotgames.com/docs/valorant
- VALORANT replay functionality includes perspectives and timeline control in the **game client**, not a guaranteed publicly documented API for extracting telemetry or replay file contents. https://playvalorant.com/en-us/news/dev/replays-everything-you-need-to-know/
- Riot's policy says product registration is needed for products serving players; player-specific public stats require appropriate opt-in/RSO integration. RSO requires a production key. Its prohibited use-case examples include **seeing opponents' stats before a match**, and **live assistance altering immediate gameplay**. https://developer.riotgames.com/docs/valorant
- Official VALORANT esports data can be available under terms from GRID/VALORANT Data Portal. Access/fields may differ by contract; treat as an optional licensed enterprise data adapter, not a default free feed. Relevant resources: https://grid.gg/ and https://docs.grid.gg/public/documentation/api-documentation/in-game-data/grid-file-download-api
- Riot General Policies prohibit products that grant unfair advantages and require legal disclaimers. Review https://developer.riotgames.com/policies/general for current text before launch.

## Allowed-first development strategy

1. Synthetic match and event fixtures with synthetic player names for unit/E2E tests.
2. Own gameplay recordings and voluntary player/teammate uploads with appropriate rights to process, share, store and derive analytics.
3. Manually annotated **post-match** footage and review; collect consent/rights declarations and annotate only observable events.
4. Ask for Riot/rights-holder authorization before indexing identified other players, expanding public access, commercial team scouting or integrating official APIs.
5. GRID adapter requires distinct business arrangement and field verification; implement only after credentials, agreement and approved usage are confirmed.

### Important nuance for esports coaching

Pre-match opponent scouting based on player-specific data is listed by Riot as **unapproved** for ordinary VALORANT developer applications. A private team tool or licensed professional arrangement may involve distinct permissions; **do not assume** being a paid team makes an unapproved use case allowed. Obtain written permission/approval before implementing that specific workflow. MVP focuses on opt-in self/team post-game improvement and research on deidentified or synthetic behavior.

## Required source-rights record

On ingest require `source_type`, `uploader_user_id`, `rights_basis` (owner, consented, licensed, synthetic), `rights_reference` (internal ID, not public), `players_consent_status`, `permitted_use` (private coaching/research), `sharing_scope`, `retention_until`, `revocable`, `verified_by`, `verified_at` and status. Refuse upload publication when rights are unknown. Defaults: private, no external indexing, no sharing. A check box alone is a declaration, not proof of third-party rights.

## Governance controls

- Consent withdrawal suspends derived record visibility immediately and queues delete cascade through source, clips, feature vectors, player twins, cluster assignments, retrieval indexes and caches.
- Maintain retention expiration and deletion requests with audit evidence; backups have defined expiry/erasure process.
- Provide export of a person's own stored data, subject to law and product capabilities.
- Use explicit opt-in UI for profile publication; otherwise no public search endpoint.
- Encrypt private VODs; signed time-limited clips; member role rules and purpose-limited service tokens.
- Do not ingest voice comms or chat by default. Where uploaded media contains voices/usernames, warn uploader and consider redaction/access restrictions.
- Source identity handling: pseudonymous player IDs; never infer identities hidden by game privacy settings.
- Disallow scraping requiring login bypass, replay format reverse-engineering, anti-cheat circumvention, process memory reads, injected overlays, real-time computer vision assistance.

## Non-affiliation disclaimer for public site

"ValoMind isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc." Adapt legal boilerplate only as allowed by Riot's current policy.

## Compliance launch checklist

| Gate | MVP private dev | Public beta | Professional/team commercial |
|---|---|---|---|
| Synthetic and owned footage only | Yes | No assumption | No assumption |
| Content rights, deletion, access scopes | Required | Required | Required plus contracts |
| Riot product registration / review | Evaluate early | Required per policy | Required + seek explicit approval |
| RSO opt-in for player-linked official data | Not needed for offline synthetic testing | Required if applicable | Required if applicable |
| Pre-match opposing-player scouting | Disabled | Disabled | Only under explicit authorization |
| Live game overlay/recommendation | Disabled | Disabled | Disabled absent explicit policy approval |
| Official esports telemetry | Disabled | Licensed only | License and field-level validation |
| Monetization | Not in MVP | Policy/registration/free tier check | Contracts/policy review |

## Compliance gate automated tests

`permission=false` prevents source upload promotion, no external provider enabled by default, synthetic records display banner, user deletion invalidates embeddings, cross-tenant accesses denied, pre-match scouting route nonexistent, recordings cannot be served by public static path.
