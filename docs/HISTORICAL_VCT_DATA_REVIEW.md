# Historical VCT dataset review

Checked 20 October 2026 using Kaggle's public metadata/file-list APIs and actual
CSV downloads. Raw downloads and reports stay in ignored `results/kaggle_review`;
no player records are committed or published. This is an audit, not a verified
identity import or a trained playstyle model.

| Source | Checked material | Usefulness |
|---|---|---|
| [Ryan Luong: VCT 2021–2026](https://www.kaggle.com/datasets/ryanluong1/valorant-champion-tour-2021-2023-data) | Metadata version 47; full player-ID lookup, 15,654 rows; partial 2023 overview and kills CSVs | Best candidate for stable provider IDs, historical map/agent assignments, performance and context |
| [Masters Tokyo playoffs](https://www.kaggle.com/datasets/mercmayhem/vct-masters-tokyo-playoffs-player-performance) | Entire CSV, 480 rows, 40 display names, June 2023 | Useful small audit/normalization pilot; 350 map rows and 130 All Maps summaries |
| [Champions LA 2023](https://www.kaggle.com/datasets/jiyaaapatel/2023-valorant-champions-los-angeles-stats) | Entire CSV, 40 rows, 40 display names | Tournament aggregates only; low priority for contextual behavior modeling |

The first dataset's URL still says 2021–2023; its current title and documentation
cover 2021–2026. Inspected 2023 overview fields include tournament, stage, match,
map, player, team, agent, side, combat statistics and opening kill/death counts.
The inspected kills table contains opponent kill totals, not a frame-aligned kill
timeline. The attempted `matches/rounds.csv` path did not exist; do not assume
specific filenames or infer event timestamps from aggregate tables. Full large
tables and complete yearly coverage have not been audited.

Publisher-reported caveats include missing loadout value from Masters Toronto
2025 onward, unavailable China statistics and zero pick rates for agents before
release. Preserve actual missingness. The literal player handle `nan` is valid;
names and team abbreviations are not reliable identifiers. Kaggle reports MIT
for the large dataset, CC0 for Tokyo, and unspecified other terms for LA. These
are uploader declarations, not confirmation of upstream rights or player consent.
Retain provider/source terms and provenance with any approved import.

Tokyo has separate `*_all`, `*_attack`, `*_defend` columns as well as combined text
fields. Do not sum the three views or combine All Maps rows with their component
maps. Map strings include a series ordinal, e.g. `2 Bind`; retain the ordinal
before normalizing the map label. All 130 aggregate rows have a blank agent.
The original file has no stable player IDs: a name-only join is a proposal.
There were no byte-for-byte duplicate parsed rows in this checked file.

LA is encoded as CP1252 in the checked download. Its fields include kills,
deaths, KAST, role and rounds, but no map/agent/match/date breakdown. Do not use
its role label as the player's permanent playstyle. Nationality, prize and rank
are unnecessary for our gameplay behavior feature set and should be excluded.

## How these data should enter ValoMind

Use separate historical performance/context tables alongside video evidence.
Keep provider IDs namespaced and resolve them through an explicitly reviewed
crosswalk to canonical players and source-scoped OCR handles. Store team
membership and agent picks per match/map with dates, never as permanent player
attributes. Deduplicate by provider match/game/player/side keys where available;
flag unresolved identifiers rather than inventing them.

Retain patch, map version, side, agent, composition and team as context. Patches
and rotations can change within a year, so year alone is insufficient. Unknown
patch/composition remains unknown until verified. Agent pick history and ACS/KD
are context/performance, not intrinsic player style. Scoreboard opening kills per
round can describe outcomes; they cannot identify first-contact propensity,
utility opportunities, trade attempts, aim response, thoughts or emotions.

Build behavioral rates from eligible opportunities in reviewed footage. Compare
only overlapping contexts, with support/missing masks and recency/patch drift
reported. Do not assume historical playstyle is fixed. Train on earlier whole
matches and test on later whole matches; also evaluate held-out players/maps/agents
where sample support allows. Keep old statistics as covariates or a separate
performance baseline, not automatic labels for YOLO/ViT training.

## Reproduce the audit

```powershell
uv run python scripts/audit_historical_vct.py results/kaggle_review/mercmayhem.csv --output results/kaggle_review/tokyo_audit.json
uv run python scripts/audit_historical_vct.py results/kaggle_review/jiyaaapatel.csv --encoding cp1252 --output results/kaggle_review/la_audit.json
```

The updated notebook also accepts `HISTORICAL_CSV` from an attached Kaggle dataset
or Drive and writes a checksum-keyed JSON audit. It reports rows, aggregates,
missingness, exact duplicates, dates and unresolved identity status. It does not
silently ingest records into player profiles. Next integration work is the stable
ID crosswalk and a versioned per-map performance adapter, after full-table audit.
