# VALORANT rules and broadcast interpretation

Checked 21 October 2026. This supports PRD-03/04 evidence-grounded annotation and
context features. Game rules, tournament rules and broadcast graphics are separate
inputs. A timer is evidence, not a complete phase detector. Rules must be selected
for the source's event/date/mode; current rules do not retroactively label old VODs.

## Rules relevant to extraction

- Standard live pre-plant rounds use a 100-second (1:40) clock, not 1:30. Buy time
  precedes this. The Spike introduces a separate post-plant countdown; do not add
  pre-plant and post-plant clocks into a fixed round length. The active round can
  finish early. Keep durations as mode-specific configuration rather than a video
  segmentation schedule.
- [Riot's beginner guide](https://playvalorant.com/en-us/news/announcements/beginners-guide/)
  confirms buying before each round, attackers/defenders and the switch after
  twelve rounds. A team is not permanently attacking or defending. Overtime side
  assignment needs its own reviewed starting-side mapping.
- A planted Spike has a 45-second objective window in the standard mode; see the
  [competition organizer's overview](https://help.playvs.com/en/articles/8659612-what-is-valorant).
  A missing numeric clock does not establish a plant. Riot documents the pulsing
  planted-Spike HUD icon in [patch 0.50](https://playvalorant.com/en-us/news/game-updates/valorant-patch-notes-0-50/).
  The current extractor recognizes explicit text, not that icon.
- The [2026 VCT global competition rules, section 6.1](https://cdn.sanity.io/files/dsfx7636/news_live/f600a428dbcb54cff5814750f4c4be2b699d7934.pdf)
  specify 60-second tactical timeouts, twice per team in regulation, with a separate
  overtime timeout. Timing begins once both coaches can communicate. Technical
  pauses are distinct. Do not hardcode all pauses to 90 seconds or infer the
  official timeout length from a broadcast countdown. Event-specific rules can
  supplement the general rules.
- [Riot patch 2.09](https://playvalorant.com/en-gb/news/game-updates/valorant-patch-notes-2-09/)
  documents observer utility/player-label colors matching team colors. Color is a
  display association, not a permanent tactical-side or player identifier. Verify
  each broadcast's palette, team mapping and side changes using the HUD and
  objective/side indicators. Screen left/right is a display slot, not attack/defense.

## Implemented HUD proposals

`round_context.csv` is exported alongside the roster. It retains video/source hash,
sample/frame timestamp, observed central clock/round label, phase, rule version and
reason. Every row is proposed; sparse sampling does not yield exact boundaries.

The precedence is replay, explicit technical pause, timeout, pause/halftime, buy
text, Spike-planted text, round-result text, then clock/layout candidates. A short
clock plus the inspected buy roster layout suggests buy phase. A clock greater
than 45 and at most 100 seconds plus a round label and sidebar layout suggests an
active round. These are candidates, not validated predictions. Conflicting/missing
clocks, low evidence and short sidebar clocks stay unknown. A bare 1:30 is not
automatically a timeout; a bare 0:20 is not automatically buy phase. No prior state
is carried through a highlight cut.

POV window proposals omit centers marked buy, pause, replay or round-result by
this export. The surrounding window still requires camera/boundary review. Buy
frames remain useful for roster/economy data and are not discarded from OCR.
The broader segment category `gameplay` means admitted match HUD, which can include
buy phase; it never certified active combat.

Local replay on the latest results produced 60 context rows: ten buy candidates,
14 active candidates, two explicit-text post-plant proposals and 34 unknown.
This is diagnostic coverage, not phase accuracy. No timeout example was validated
in this two-minute sample. Tests cover 90-second timeout text, technical pauses,
short-clock ambiguity, replay precedence and side changes.

## Minimap extraction and next measurements

The notebook saves `minimap_review/` crops from existing segment-review images
and a `minimap_review_suggestions.csv` template. The crop profile is scoped to the
inspected source `omjZXmc7_4A`; other layouts remain unsupported until calibrated.
Review that a map is present and the crop includes it before annotating markers.
Player/team IDs, side, normalized marker coordinates and map regions start empty.
World coordinates remain empty. No marker detector, identity tracker, tactical
action classifier or team-side color calibration is claimed.

Useful future outputs are per-player map-image positions, region occupancy,
routes, site arrivals, rotations and team spacing. Each requires evidence:

- Identify player markers/portraits/numbers and match them to reviewed roster IDs;
  ambiguous icons remain unknown. Spectator markers may show information players
  could not see. Marker visibility must not become player knowledge.
- Calibrate crop bounds, rotation, zoom, map patch/version and region polygons.
  Image coordinates are not game-world coordinates. Distances are not meters
  without a verified transform. Teleports, deaths and POV changes can break tracks.
- Preserve team display color separately from tactical side. Review initial sides,
  halftime and overtime. Do not globally equate red/teal with attack/defense.
- Derive observable movement from continuous tracks before labeling tactics. Moving
  toward B does not prove a rotation decision; standing alone does not prove a lurk.
  Utility ownership, trades and coordination need synchronized event evidence.

The first minimap training target should be icon localization and identity
association, evaluated on unseen complete matches. Cross-role playstyle features
follow only after reliable tracks, contexts and opportunity denominators exist.
