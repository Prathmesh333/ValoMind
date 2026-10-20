# Third cloud export — 2026-10-20

Inspected D:/Downloads/valomind_results (2).zip without modifying it. The run uses
video_v4, crop_retry_v1, hud_rules_v2 and roster profile vct_1080_v2 on the same
120-second source preview. GPU device 0 is configured; exact physical hardware is
not established by the manifest. No detector weights or portrait classifier/reference
were configured. Copied metadata/CSVs and 12 segment review JPEGs into results/run_3_review.

| Output | Previous run | This run |
|---|---:|---:|
| Sampled frames | 60 | 60 |
| Admitted gameplay frames | 32 | 32 |
| OCR observations | 2052 | 2071 |
| Roster observations | 319 | 320 |
| Known-team observations | 274 | 315 |
| Unknown-team observations | 45 | 5 |
| Known-agent observations | 0 | 0 |

The extra OCR rows are 18 team-crop and one player-name retry. Jamppi at 28.028s is
now present. All ten handles occur in each of the 32 admitted frames. Forty old
unknown team fields were resolved, and the newly recovered Jamppi row also has a
team, yielding 41 additional known-team rows overall. No previously nonempty team
assignment changed. Five team fields remain unknown: the 100T roster at 26.026s.
No incomplete or duplicate roster slots remain among admitted frames.

Repeated the earlier six-frame visual-reference comparison without changing the
reference labels. All 60 names, teams and map entries now match those assistant
references; agents remain unresolved on all 60. No extra rows in those frames.
References are still assistant proposals, not independent verified ground truth,
and these counts are not full-video accuracy. Files are under run_3_review/comparison.

The archive includes 320 portrait crops and 12 segment review images. Portrait
extraction is functioning, but agent IDs being blank is expected with portrait_matcher
null. Do not interpret that as a trained classifier failing to recognize agents.

Visually checked the 12 segment review JPEGs in a contact sheet. Ten show match HUD
and two show a map establishing shot/player-camera cut. Four visibly HUD-present
samples, at about 10, 20, 30 and 40 seconds, are still marked uncertain. The other
six HUD samples were admitted. This exposes a remaining gate-recall problem even
though roster extraction improved. Saved proposed visual segment references in
segment_assistant_reference.csv; they are not scored as independently reviewed.
No replay-marked example is present in this small sheet, so replay behavior remains
unvalidated. Review images cover sampled instants, not every cut or segment boundary.

Next priority: improve the gate using spatial HUD evidence/temporal confirmation
while retaining uncertainty on camera cuts, then benchmark against reviewed segment
labels. Retry the remaining left team crop at 26.026s rather than assuming membership.
For agents, independently review/expand the 320 portraits and provide a trained
character classifier; generic YOLO detection cannot identify portrait characters.
No code/model changes or additional neural training were made during this result review.
