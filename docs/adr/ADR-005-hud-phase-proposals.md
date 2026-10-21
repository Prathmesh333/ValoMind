# ADR-005: Separate HUD admission from round-phase proposals

Date: 21 October 2026. Status: accepted for the private offline notebook.

The broadcast admission rules retained buy and active-round frames under a broad
gameplay category. This is useful for roster OCR but poor for choosing combat
review windows. Timer values overlap across buy, round, pause and result states;
highlight edits prevent time-only reconstruction.

Keep existing segment and observation schemas unchanged. Add a separately
versioned `round_context.csv` derived from central clock/round OCR, explicit state
text and roster layout. Unknown remains an output. Omit proposed buy/pause/result
centers when choosing POV windows, but retain their OCR/roster records. The
window's complete continuity still needs review.

Review-only minimap crops use an explicitly scoped source profile. Empty marker
coordinates and unknown sides are preferred to fabricated tracks. No team-side
color assumptions or psychological labels are introduced. Original source rights
and review provenance remain unchanged. Tests cover timer ambiguity and side
changes; the new rules have not been independently evaluated for accuracy.
