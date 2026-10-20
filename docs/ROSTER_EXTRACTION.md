# Spatial roster extraction

Implemented the two inspected VCT layouts: buy-phase bottom rosters and gameplay
sidebars. Names must lie inside the configured roster-name region. World labels,
facecam captions and other screen text cannot establish a roster record. The top
left CURRENT map label is parsed separately; NEXT labels are not current-map facts.
Top scoreboard team names are associated with the corresponding left/right roster
in the same frame. Missing or conflicting team OCR remains unknown. Left/right is
screen position, not attack/defense.

Aliases are explicitly scoped to omjZXmc7_4A. I0OT/10OT resolve to 100T only inside
the team-name region. Display handles have source-scoped IDs, not verified global
player identities. No player belongs permanently to the displayed team or character.
Another video requires a reviewed catalog and matching layout; this is not yet a
general multi-tournament parser. Call process with roster_catalog to provide one.
The catalog has players, teams and maps alias dictionaries with normalized keys.

The existing second-run OCR now produces 319 roster observations, ten displayed
handles and current-map Split on every row. Team associations are proposed on 274
rows, with 45 unknown. There are 20 buy-layout and 299 sidebar rows. Counts represent
repeated frame observations, not distinct players, rounds or matches. One expected
name observation is omitted due to OCR/ambiguity thresholds; nothing is filled in.

Reprocess existing exports without video/GPU:

```powershell
uv run python scripts/parse_roster_export.py results/run_2_review/observations.csv
```

Output roster_observations.csv includes source timestamp, map, side/slot, player
handle, proposed team, evidence observation ID, per-field OCR confidence and portrait
coordinates. Confidence is not calibrated probability. Agent IDs remain blank.
Each record is proposed and must be reviewed before becoming training ground truth
or canonical evidence. Grouping frames into complete map games/series is still pending.

The updated standalone notebook exports roster CSVs for each job and a merged
roster CSV. video_v3 adds actual frame dimensions to CSV records for scaling the
layout. Changes to catalog/profile are included in job identity. Known-layout
portrait crops are saved before frame commit, so failed writes can retry. They are
named with roster_observation_id under portrait_proposals/ for review and labeling.
No portrait is labeled from inferred player preference or presumed agent pick.

For the current local result, exported 20 portrait samples: one per displayed
handle/layout, with blank character labels and source provenance. See
results/portrait_review_v1.zip. An independently labeled, varied portrait dataset
is still needed for classifier training; no trained classifier is claimed.

Validation covers current-versus-next map parsing, both layouts, coordinate scaling,
missing/conflicting teams, duplicate identities and unknown video catalogs. Existing
pipeline tests cover resume and skipped frames. The source-specific roster parser
was run on actual exported OCR; a new full cloud run with crop output remains pending.
