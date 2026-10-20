# First cloud export review — 2026-10-20

Source: omjZXmc7_4A. Export metadata identifies VIT vs. 100T match highlights,
3373 seconds (56m13s), 1080p, nominal 60fps. Source rights remain unconfirmed.

Observed run: video_v2, hud_rules_v1, interval 2s, END_SECONDS=120, device=0,
EasyOCR 1.7.2. No custom detector weights and an empty identity catalog. GPU 0 was
configured; the archive does not establish that the physical device was a T4.

Result: 60 sampled frames, all uncertain/review, zero observation rows. The CSV
was empty because the gate rejected every sample, not because extraction succeeded
with zero players. Saved probe text contained round labels and map-order strips,
and often read timer separators as periods. Existing confidence filtering and the
requirement for two independently readable scores were too brittle for this HUD.

Inspected decoded source frames at 10s, 30s and 90s were exported locally; the 30s
frame was visually inspected and shows gameplay, top map/round/score HUD and both
five-player sidebars. Source decoding works. This is a filter failure, not evidence
that the first two minutes contained no gameplay.

Fix: hud_rules_v2 accepts period-separated timers and the combined VCT current/
next-map strip plus round-label signature. Probe threshold changed from .5 to .3;
confidence is now retained per probe item for diagnosis. Replay/break rules still
take precedence. Rules changes create a new job identity, so old completed samples
will not silently skip revised processing. Notebook rebuilt with the new worker.

Replaying the 60 stored OCR text lists through revised rules yields 53 extraction
decisions and 7 review decisions. This is a diagnostic replay, not fresh OCR or a
measured precision/recall benchmark: the old export lacks per-item confidence, so
the replay uses all stored text. A new Colab preview is required to verify full
OCR output with the revised confidence gate. No new player identities, agent
assignments or observation CSVs were fabricated from the diagnostic replay.

The original archive included the entire video (about 1.68 GB). Future notebook
archives exclude downloaded video by default while retaining metadata, job state,
CSVs and training artifacts. The original results ZIP is preserved.
