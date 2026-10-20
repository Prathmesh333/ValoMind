# Gameplay admission and remaining team label — video_v5

The third cloud run showed real HUD at 10, 20, 30 and 40 seconds while the gate
returned uncertain. Inspection of saved OCR exposed weak round-label confidence
and transient loss of one score. The two-consecutive-sample rule then prolonged
the missed extraction despite other clear same-frame HUD evidence.

hud_rules_v3 distinguishes strong compound evidence from weak candidates. A
CURRENT/NEXT map strip plus a central timer or round label can admit gameplay
immediately. Current captured OCR records include box coordinates: map-strip text
must lie in the upper-left strip, and timer/round text in the upper-center HUD.
Weak candidates still require consecutive samples. Uncertain frames never inherit
gameplay permission from the previous frame, and explicit replay/break markers
still take precedence. This is a layout-specific heuristic, not a trained classifier.

Replayed all 60 saved probe transcripts: 55 now admit extraction versus 32 before,
with five remaining in review. All four visually checked missed gameplay samples
are recovered; the player-camera sample at 60.060s remains uncertain. Legacy probe
records lack coordinates, so this is a transcript diagnostic, not a new cloud run
or validation of spatial OCR behavior. Five saved probes are included as regression
fixtures; separate tests cover spatial placement, state breaks and replay precedence.

The remaining five team blanks at 26.026s came from OCR IQOT at confidence .3823.
Visually inspected that exact frame's scoreboard, which shows 100T. Added IQOT as
a source-specific team-region alias, without reducing thresholds or changing player
name normalization. Reparsed the existing OCR: all 320 roster rows now have a team,
with no incomplete or conflicting slots. The new roster profile is vct_1080_v3.
Original run exports are preserved. This result covers only already admitted frames;
it does not fabricate roster entries for newly proposed extraction frames.

Artifacts: results/filter_v5_diagnostic/saved_probe_replay.csv, roster_reparse.csv,
roster_audit.json and team_evidence_26026.jpg. Notebook rebuilt with video_v5.
Agent classification remains optional and untrained; this patch makes no agent
recognition claim. A fresh 120-second Colab run is required to measure actual
end-to-end coverage, and independently reviewed filler/replay/other-layout samples
are still needed before generalizing the gate to full broadcasts.
