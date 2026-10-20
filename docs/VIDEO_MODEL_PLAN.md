# Video and behavior model plan

The recommended design has two separate learning problems:
`authorized video -> reviewed events -> contextual behavior features -> style comparison`.
Train video extraction only after a manual annotation workflow provides trustworthy
examples. Player style does not require an end-to-end video model or an LLM fine-tune.

## First dataset

Start with a planning pilot of 10–20 owned or explicitly permissioned matches,
one map and one recording layout. This is a labeling and feasibility pilot, not
enough evidence to promise a reliable model. Include multiple players and character
roles. If player behavior is the goal, prefer known-player POV recordings; broadcast
camera switches complicate attribution. Preserve recording layout, patch, resolution,
frame rate, source checksum and time origin. Establish rights for training and
derived models, retention and withdrawal before including real footage.

Label round boundaries, deaths, spike plant/defuse and visible utility use first.
Record negative examples and eligible opportunities, not just successful actions.
Keep source/evidence time ranges, player, map, side, patch, annotation version,
reviewer, visible fields and unknown fields. Double-label at least 10% to measure
agreement. Model proposals stay unverified until independently reviewed.

## Video extraction

Begin with offline FFmpeg preprocessing and fixed HUD regions using OCR/templates.
Benchmark this against human labels before training. Add a small pretrained image
detector if HUD variation defeats templates. For events requiring motion, compare
a pretrained short-clip video classifier with the simple baseline and fine-tune
only if held-out performance and review-time savings justify it. Generic video
weights do not already understand VALORANT tactical behavior. Torchvision provides
[pretrained video model families](https://docs.pytorch.org/vision/stable/models.html).

Use low-rate sampling for persistent HUD state and denser short windows around
candidate transitions; tune rates against timestamp error rather than assuming
one frame rate works for every event. A single POV cannot supply all ten players'
positions or hidden information. Keep those values null. Minimap coordinates need
map-specific calibration and visibility checks before downstream use.

## Player style

Build transparent opportunity-normalized rates from reviewed events. Compare only
shared situations and adequately observed dimensions. Keep character role as
context and a confounding diagnostic. Fit scalers and contextual baselines on
training data only. Start with weighted distance, then evaluate agglomerative
clustering or HDBSCAN once enough players have coverage. Return insufficient data
when appropriate; do not manufacture similarity percentages.

Later action prediction can start with logistic regression or boosted trees on
event sequences. Evaluate a temporal neural model only after these baselines.
CoachAI should retrieve these results and evidence; training an LLM is not needed
for the first useful coaching experience.

## Evaluation and compute

Keep all clips, overlapping windows and alternate recordings from one match in one
partition. Use separate player-held-out tests for unseen-player generalization and
a chronological held-out set for patch/time drift. Within-player forecasting needs
its own chronological protocol. Random frame splitting leaks near-identical images.
[Grouped cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html)
supports match grouping; chronological restrictions need additional split logic.

For extraction, report per-event precision/recall, false positives per video hour,
timestamp error, review corrections and processing cost. For style, report shared
opportunities, neighbor stability, role leakage and blinded coach judgments. For
prediction, compare macro-F1, log loss, Brier score, calibration and abstention
against majority-action and role-only baselines. Set acceptance thresholds after
measuring pilot baselines; no accuracy guarantee is justified yet.

CPU is sufficient for the annotation MVP and initial statistical baselines. Choose
GPU rental or purchase only after profiling a selected model with representative
clips. Save dataset manifests, splits, code/model/schema versions and checkpoints.
Consent withdrawal must remove training eligibility and identify affected model
artifacts for retirement or retraining; deleting a video does not erase learned weights.

Riot's [current VALORANT developer policies](https://developer.riotgames.com/docs/valorant)
require product review/registration and applicable player opt-in; keep the product
offline and permission based. Official APIs are not assumed to provide full trajectories.
No footage has been acquired or used for training in this increment.
