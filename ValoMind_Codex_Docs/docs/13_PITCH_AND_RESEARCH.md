# 13 — Esports Portfolio Pitch, Coach Pilot, Publication Path

## Portfolio positioning

**ValoMind — explainable multi-agent player intelligence for VALORANT.** From authorized retrospective gameplay, ValoMind builds time-evolving player behavioral models, finds stylistic similarities across different playable character roles and lineups, and lets coaches ask questions answered with annotated match evidence. A research track studies calibrated conditional player-action prediction and team composition interactions.

## Unique differentiator

"Two human players can play different character roles and select very different VALORANT agents yet exhibit similar decision patterns. ValoMind tries to measure that similarity fairly by accounting for opportunities and game context instead of clustering by their selected characters."

This is not just replay summaries, heatmaps, K/D dashboards or prompt-wrapped statistics. Prove via blind coach evaluation and cross-agent generalization experiments.

## Portfolio demonstration script (5–7 minutes)

1. Explain problem: match VOD insights are manual and biased by character classes.
2. Open **clearly synthetic** authorized demo with player A (Duelist), B (Sentinel), C (Duelist).
3. Filter to equivalent verified opportunities; show A/B nearer than A/C **despite roles**. Highlight denominators and uncertainty.
4. Open clips supporting feature similarities and exceptions.
5. Ask CoachAI: "What repeated decisions are observed across these players?" Show citations and abstention when evidence absent.
6. Switch composition; show same player's behavior contextual breakdown, not identity rewrite.
7. Discuss evaluation, policies, and next experiments. Never claim access to private pro data.

## Artifacts to publish

- Responsible public demo on synthetic/openly permissioned data; no real player profiling without rights.
- GitHub repo with reproducible tests and architecture diagrams.
- Short screencast of upload-to-insight and cross-role analysis, synthetic label clearly visible.
- Technical report on features, denominators, clustering, bias tests, null handling and coach ratings.
- Privacy & game-integrity checklist and limitations.

## Proposed research questions

RQ1: Can context-normalized behavior vectors recover human-reviewed style similarities **across character roles** better than role-based or aggregate performance baselines?

RQ2: How stable are player category memberships across map, patch, side, composition and time?

RQ3: Does explicit teammate/lineup composition conditioning improve explanation fidelity and predictive calibration without encoding character-role shortcuts?

RQ4: Do evidence-backed LLM reports save coaches review time and decrease unsupported statements versus ungrounded summaries?

## Experiment design

Collect authorized VODs with balanced players and characters where possible; annotate key tactical opportunities with inter-annotator agreement; preregister within-player time splits and held-out characters; compare against random neighbors, same-role retrieval, K/D and ACS baselines. Conduct blinded panel of coaches or advanced players who judge matching tactical clips; report effect sizes, confidence intervals, sample counts, and errors. Avoid training/test leakage from same match/round or mirrored clips.

## Outreach positioning

"I'm building a permission-based VALORANT coaching research platform that models player decision tendencies and clusters similar playstyles even across character roles. The prototype focuses on evidence-backed VOD analysis, and I'm looking for coach feedback on which tactical behaviors are most useful to review." Make demonstrably true claims only.

## Potential future business direction

After permission/approval: voluntary player coaching workflows, organization-private retrospective performance reports, analyst labeling software, team review and research partnerships. Public player indexing, pre-match opponent scouting, and subscription marketing require specific policy and rights review; not roadmap promises.
