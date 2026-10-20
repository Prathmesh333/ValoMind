# Second cloud export — 2026-10-20

Inspected D:/Downloads/valomind_results (1).zip as data. Original archive preserved.
Copied the job manifest and CSVs into results/run_2_review for local inspection.

Both runs cover the first 120 seconds of omjZXmc7_4A, sampled every 2 seconds,
using EasyOCR 1.7.2, configured device 0, no custom detector and no alias catalog.
The second run uses hud_rules_v2, and both refer to the same source SHA-256.

| Result | First run | Second run |
|---|---:|---:|
| Sampled frames | 60 | 60 |
| Admitted gameplay frames | 0 | 32 |
| Uncertain/review frames | 60 | 28 |
| OCR observation rows | 0 | 2052 |
| Resolved entity rows | 0 | 0 |

The new classifier proposes gameplay on 43 samples; transition confirmation admits
32. Seventeen raw candidates lack a reliable signature; eleven more frames are
held for transition confirmation. These counts measure processing coverage, not
classification accuracy. This preview contains no detected filler or replay class,
so it does not validate either of those categories or full-video performance.

All ten sidebar player strings recur: Cryo, bang, Vora, Asuna, Timotino, Chronicle,
Derke, Jamppi, Sayonara and PROFEK. These are observed OCR text, not verified person
IDs or confirmed membership records. Duplicate appearances in one frame mean
string counts are not round, appearance or participation counts.

CURRENT: SPLIT occurs in all 32 admitted frames. That is evidence for a current-map
text parser, not a claim that NEXT: SUMMIT or NEXT: LOTUS are current map games.
Team text I0OT occurs 28 times while exact 100T occurs once, illustrating the need
for reviewed aliases and spatial team-name crops. Do not globally replace I/O
characters in player names. VIT appears 29 times.

1309 OCR rows have model confidence >= .8, while 207 are below .3. OCR confidence
is not calibrated correctness. No agent portraits were classified. All IDs remain
blank because no catalog was configured. No YOLO training or detection happened.

Next useful increment: parse roster rows from the reviewed HUD layouts and match
names to stable, reviewed aliases; read current map separately from next-map text;
classify cropped agent portraits; compare outputs to independently reviewed labels.
The gate needs additional labeled samples around missed gameplay and actual
fillers/replays before thresholds are changed again. The earlier 53-frame result
was only a replay of all saved text without per-item confidence, so it was not a
prediction of the actual rerun's accepted-frame count.
