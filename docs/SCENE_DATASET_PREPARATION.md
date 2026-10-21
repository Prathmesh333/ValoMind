# Scene proposal staging

`scripts/prepare_scene_proposals.py` stages scene labels for review. It supports
PRD-03 evidence provenance without treating assistant annotations as independent
verification. It does not train a model or complete the annotation milestone.

```powershell
uv run python scripts/prepare_scene_proposals.py results/run_5_review/annotation_pass_2 results/scene_dataset_provisional_v1
```

The input folder contains `scene_segments_proposed.csv` and
`frame_labels_proposed.csv` from the private annotation pass. Frame paths may
reference neighboring extracted results but must stay within that review workspace.
Use a new output directory; the script never overwrites existing review data.

It copies original JPEGs at intervals of at least 250 ms, excludes uncertain
transitions and intervals shorter than 500 ms, and leaves a 100 ms boundary margin.
Source/frame checksums and interval IDs remain attached. Identical images with
conflicting labels or cross-window frame assignments cause an error.

Scene class and camera perspective are separate targets: buy phase, for example,
can appear as either first person or an observer view. No player trait, emotion,
intent, reaction time or tactical decision label is generated.

Every output is `proposed`, `training_eligible=false`, `split=unassigned`, with
independent review pending. There are no fabricated reviewer decisions or automatic
training approvals. The directory deliberately has no YOLO train/val class layout.
Additional reviewed sources, match grouping and a documented split policy are
required before supervised model training and evaluation. All windows from a
source must stay in one group; multiple videos of the same match must be grouped
together once match identity is verified.

The current private pilot produced 91 samples from one source: 3 establishing,
28 buy, 56 active-gameplay, 2 player-camera and 2 death-animation images. These
counts describe a small imbalanced proposal set, not a generalizable benchmark.
Raw images, player records and private review decisions remain excluded from Git.
