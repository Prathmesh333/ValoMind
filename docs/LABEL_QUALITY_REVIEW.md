# Label quality inspection — 2026-10-20

Inspected the 20 portrait crops as a contact sheet and checked roster proposal
consistency across the 32 admitted frames. Reviewed the seed box generator against
the already inspected 10s, 30s and 90s source frames. These are assistant visual
checks, not independent human verification or a calibrated accuracy benchmark.

All 20 portrait crops show recognizable character artwork. Proposed labels:
Chamber (Cryo), Viper (bang/Sayonara), Fade (Vora/Jamppi), Omen (Asuna/PROFEK),
Neon (Timotino/Chronicle), Yoru (Derke). They belong to these inspected frames,
not permanent player preferences. Saved in results/portrait_review_v2.zip while
preserving v1. Labels remain proposed with independent review pending.

Dataset limitations: 20 portraits represent only six character classes; Chamber
and Yoru have two samples each, other classes have four. They are repeated samples
from one map/video. Sidebar portraits include small background/health-bar/overlay
fragments and buy-phase crops have a different aspect ratio. A classifier could
learn layout/team-color shortcuts. Standardize crops/padding and evaluate across
layouts and teams; retain unknown/occluded/dead-player examples rather than forcing
every crop into one of these six characters. Do not stretch all faces arbitrarily.

The 102 HUD boxes are approximate proposals across three images; no clear
player/portrait row mismatch was found in the inspected layouts. This does not
establish precise per-box IoU. Training and validation share source, map and players,
so a high score on the seed cannot establish generalization. More labels and
independent-broadcast evaluation are necessary before trusting any trained model.

Roster audit: 319 rows across 32 frames; no duplicate player/slot conflict, and no
player appears under both team IDs in this preview. 45 rows have unknown team.
The single missing roster entry is right slot 3 at 28.028s: OCR reads Jamppi at
confidence .4498, below the .5 admission threshold. This is a recoverable text
recognition case, not an invisible player. Keep the threshold; use a dedicated
name-region OCR retry or explicitly labeled temporal inference in a later step.

Added an audit CLI that reports missing slots, unresolved fields and duplicate
assignments. Added a parser guard against assigning the same detected team to both
scoreboard sides, with a version bump to vct_1080_v2 and regression coverage.
No trained detector or portrait classifier was evaluated; neither exists yet.

Recommended order: (1) crop-level OCR retry for known name/team regions, (2) expand
reviewed HUD/portrait labels with negative and low-quality examples, (3) train small
detector/classifier baselines, (4) evaluate on a different full broadcast. Only then
consider teacher distillation or model-size changes. The present bottlenecks are
coverage, source diversity and field recognition, not demonstrated model capacity.
