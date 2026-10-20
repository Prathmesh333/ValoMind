# 01 — Product Requirements Document (PRD)

## Vision
ValoMind helps players, analysts, coaches and authorized teams understand **observable tactical behavior** via offline footage review, data-backed player similarity, and contextual AI coaching. The long-term research goal is agent-based behavioral prediction, not synthetic imitation of a person's inner thoughts.

## Target users and jobs-to-be-done

| User | Job | First deliverable |
|---|---|---|
| Individual player | Understand recurring decisions from own replays | private improvement report, clips |
| Analyst | Efficiently label, search and compare many rounds | VOD timeline and event review |
| Coach | Identify repeatable strengths/weaknesses, review tactics | CoachAI question with evidence |
| Performance researcher | Measure whether playstyle is persistent across character roles | cross-role cluster analysis |
| Team lead (later, authorized only) | Compare lineup behaviors | retrospective team-composition report |

## User stories with acceptance criteria

- **PRD-01** As an authorized analyst, I can create workspace, grant `viewer`, `analyst`, `coach` permissions and view audit trail. Non-members cannot load content by guessed IDs.
- **PRD-02** I can upload one rights-cleared video plus a source rights declaration. Unsupported formats fail with clear error. Re-upload with same hash deduplicates.
- **PRD-03** I can annotate a round time range, relevant players and observed movement/decision/utility events, then submit for review. Editable draft is never silently considered verified ground truth.
- **PRD-04** I can see player profiles over a selected patch/map/time range; rates show numerator, denominator, sample coverage, confidence and evidence.
- **PRD-05** I can search cross-role **style similarity** even with different VALORANT agent characters/roles; output shows similarity estimate, common behavior dimensions and invalid comparisons.
- **PRD-06** I can browse clusters/categories, their defining features, player membership confidence, variability across maps/patches, and annotator-reviewed human-readable labels.
- **PRD-07** I can ask CoachAI to explain one player's tendency and get only attributable citations to authorized clips/events, with explicit uncertainty and no mind-reading.
- **PRD-08** I can compare a player's own behavior under different VALORANT agent lineups to explore how context shifts, with an explicit 'observational' disclaimer.
- **PRD-09** I can delete a player's data or video (subject to permitted retention obligations) and all derived features/indexes are deleted or invalidated.
- **PRD-10** Users cannot access real-time match guidance, prohibited opponent pre-match scouting or features based on unauthorized gameplay extraction.

## MVP scope (M0–M3)

Included: private permissioned workspaces, video upload/metadata, manual annotation, review, feature extraction from verified annotations, player profiles, normalized similarity, role-agnostic categories, grounded Q&A, synthetic data demo, tests, observability.

Excluded: public player search, broad nonconsensual pro-player indexing, reverse-engineered replay parsing, real-time overlay, game hooking, head-to-head live prediction, private voice/text comm analysis, 'read player mind', fully physically accurate 5v5 simulation, public pre-match scouting. External official API and GRID adapters are later gates, not dependencies.

## Two distinct meanings of "agent"

1. **VALORANT character agent:** Jett, Omen, etc.; has Riot-defined class/role and abilities.
2. **ValoMind AI agent:** a service/tool-using software process (CoachAI, profile agent, team analysis agent).

Never use a column or variable simply called `agent` without qualifying it. A **player twin** belongs to a human/player identity; game character picks vary per match.

## Three differentiated product modules

- **ValoTwin:** longitudinal behavioral profile, evidence and temporal changes.
- **StyleMap:** role-agnostic player-to-player comparison, style categories, context-specific similarity, multi-label style membership.
- **CoachAI:** retrieval-and-explanation layer, QA and improvement-oriented retrospective coaching.
- **CompLab (post-MVP):** character lineup composition plus coordination analytics, clearly separate from player style.
- **StratSim (research):** bounded action-choice and tactical scenario exploration, uncertainty calibrated.

## Functional filters and UX behaviors

Filter every analysis by map, side, patch, date range, player, sample status, lineup and round phase. Default compare requires shared observable contexts. Explain when two players cannot fairly be compared. Show match count, round count, eligible opportunities and annotation quality. Make feature version and model version visible in an 'Analysis details' drawer.

## Nonfunctional targets (engineering hypotheses; validate in pilot)

- 95th percentile metadata/profile read latency < 500 ms locally on seeded demo; uploads and processing async.
- UI remains responsive when 1-hour video is uploaded; failed jobs retriable.
- Privacy: default private; server-enforced tenant isolation, authz test coverage 100% of sensitive API routes.
- Reliability: job idempotency on retry; durable job status.
- Explainability: 100% of CoachAI factual claims about gameplay linked to reviewed evidence; empty evidence produces abstention.
- Accessibility: WCAG 2.2 AA goal; keyboard usable annotation UI, timecoded transcript alternative where available.

## Commercial positioning and gating

First a demonstrable research/prototype and voluntary post-game coaching workflow. Team product requires content rights, Riot review and opt-in compliant sharing. Do not advertise as endorsed by Riot; do not promise legal/contractual approval or universal data coverage.

## Success metrics

Primary: accurately verified annotations/round, coach time to find a representative clip, rate of correct evidence citation, cross-role cluster stability and utility measured in expert blind review. Secondary: completion of upload-to-insight flow, comparison abstention rate, pilot retention, compute/storage cost per VOD. Avoid vanity 'AI accuracy' without held-out data.
