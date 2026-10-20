# 10 — Product UI, Interaction and Accessibility Specification

## Visual identity

Product: ValoMind, neutral premium esports analytics UI; do **not** copy VALORANT in-game UI, copyrighted assets, maps or official logos without permission. Dark-neutral first with mint/coral accents and legible data visualizations. Use compliant plain text game references and appropriate non-affiliation notice on public pages. All demo portraits, maps and statistics synthetic or rights-cleared.

## Navigation sitemap

```text
/sign-in
/workspace                   → overview, recent jobs, data permission status
/library                     → uploaded assets, rights, status, review
/library/[assetId]/annotate  → video + round + evidence editor
/players                     → scoped directory and search
/players/[playerId]          → profile, style, contexts, clips, evolution
/styles                      → StyleMap cross-role clusters and taxonomy
/styles/compare              → player A/B with normalizing controls
/compositions                → lineups/team coordination (post-MVP)
/coach                       → question/answer with clips and evidence ledger
/settings                    → members, privacy, deletion, model versions
/admin/jobs                  → processing status/retry (authorized)
```

## Primary screen: Player profile

Header: selected player pseudonym, data status, source rights, sample support, current behavior style tags, profile version, filters by map/side/patch/date. Tabs: `Overview`, `Behaviors`, `Similar Players`, `Contexts`, `Evidence`, `Model Details`. At least two views: role-normalized and pick/lineup-specific. No fabricated scores/claims. Prompt 'Insufficient verified examples' when low confidence.

## StyleMap screen (high priority)

- Search and compare two human players even if their selected VALORANT game roles differ.
- Default `role_normalized` with control for `context_matched` and `role_composition_breakdown`.
- Show feature similarity radar/barplot with contextual baseline and sample counts, cohort selection and high-impact dimensions.
- Cluster gallery with human-reviewed labels and representative patterns, not 'best/worst' ranking.
- Filters: map, side, round phase, patch, skill cohort if appropriate, game character role **as a diagnostic filter rather than cluster identity**.
- An interactive scatter/embedding map, with explicit note that UMAP/t-SNE visual distances are approximate, and points colored by style group not role by default; optional toggle to color by character role for confounding inspection.
- Left region: nearest peers, right region: clips for matched opportunities and a low-sample / overlap warning.

## Annotation screen

Large VOD player, frame-accurate time field if video source permits, round timeline, role/pick markers, `Observed` vs `Hypothesis` radio, map region selection, event type, opportunities context, quality slider, reviewer verify action, change history. Keyboard mappings documented and adjustable; avoid reliance on mouse-only drag interactions.

## CoachAI screen

Question composer, thread list, scoped filters and a split pane showing evidence cards with video playback. Answer uses visual labels `Observed`, `Interpretation`, `Possible coaching drill`, `Limitations`. Citations jump to bounded clips with timecodes; no generated claim should lack evidence. Handle empty/no permission/no media states.

## Composition screen (later)

Five human player slots + five VALORANT character picks, role distribution, computed composition fingerprint, team behavioral graph and changes across match contexts. Clear legend distinguishing 'agent picks', 'human player styles' and 'AI modeling components'. Side-by-side comparisons display confounders and sample size.

## UI states to implement on every page

`loading`, `empty`, `no_authorization`, `insufficient_data`, `analysis_pending`, `failed`, `stale_result`, `revoked`, `synthetic_demo`, `ready`. Ensure descriptive next steps rather than blank charts or infinite spinners.

## Synthetic-demo banner

Full-width subdued indicator 'Demonstration data — invented players and events; not a real VALORANT performance evaluation.' It must be persistent across profile, compare, CoachAI and screenshot/export flows. Never attach a real player's name to invented model values.

## A11y and responsiveness

WCAG 2.2 AA targets: all actions keyboard-operable; visible focus; captions/transcripts when available; contrast >4.5:1 for normal text; icon labels; charts have data table equivalents; clipping and player links have accessible names. Desktop first for annotator multi-pane; tablet and mobile allow read-only player reports. Timecode navigation cannot rely solely on waveform color.

## Export

Export authorized role-normalized report as PDF/CSV/JSON in later milestone with watermark, date/patch/source scope, rights notice, synthetic label and model/version provenance. Signed expiring links for clips; no raw external media URLs.
