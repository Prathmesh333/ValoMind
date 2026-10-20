# Video-assisted labels → YOLO → error review

Use the provided video as a seed for labeling and a first training smoke test.
The existing OCR pipeline has no trained custom detector yet. A vision assistant
can propose bounding boxes; those labels are not automatically verified.

The initial local seed at results/hud_seed_v1.zip contains three visually inspected
frames (10s, 30s, 90s), six region classes and 102 proposed boxes. The classes are
scoreboard, current-map label, team label, roster row, roster player name and roster
agent portrait. Player names and playable-character identities are separate OCR/
classification results, not permanent YOLO classes. This allows new teams and
players without retraining the detector for every identity.

Review and correct these labels in a YOLO-compatible annotation editor. Include
both buy-phase and sidebar layouts, dead-player rows, replays, missing HUDs and
filler negatives when expanding the dataset. A large teacher model may propose
additional labels, but retain source/time/model and review history for each label.
This first pack is a layout seed, not a production training dataset.

After review, upload the small dataset ZIP to Colab, extract it, set DATA_YAML to
the candidate.yaml path and enable the notebook's optional training cell. Use
pretrained YOLO weights as the starting point. This transfers YOLO's visual
features; copying arbitrary vision-language-model weights into YOLO is not the
proposed approach. The labeled examples connect the two architectures.

Point WEIGHTS at the resulting best.pt and run extraction on the same source to
inspect boxes, OCR crops and roster alignment. This can reveal engineering errors,
but it cannot measure generalization. The seed YAML's same-video validation is
explicitly a smoke test. Reserve another complete broadcast with independent
human labels for actual evaluation; never split adjacent frames randomly.

Prioritize corrections by missed HUD regions, wrong region class, box overlap,
OCR text errors and player-agent pairing errors. Score each stage separately:
detector boxes can be correct while the player/team attribution is wrong. Add
corrected hard examples to the next dataset version, retain the held-out broadcast,
and compare YOLO against fixed-layout crops on identical reviewed samples.

A generic large detector is not yet a competent VCT teacher. Start with reviewed
visual labels, then evaluate automated teacher proposals against them. Store teacher
outputs as proposals and stop propagating labels from cases where it is unreliable.
No teacher API, detector training or learned player identification was run here.
