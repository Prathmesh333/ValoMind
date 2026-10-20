# 07 — Character Composition, Player Roles, Team Synergy and StratSim

## Four distinct concepts

1. `human_player`: real human identity/authorized pseudonym.
2. `character_agent`: VALORANT selectable character and official game role, abilities and patch-specific metadata.
3. `composition`: set of **five** selected character agents for a team/match, plus which human played each.
4. `software_agent`: ValoMind modeling/reasoning component; never part of game team composition.

Player behavior similarity should **not** be determined by (2) or (3). But they affect the opportunities and meaning of observed behavior and therefore must be retained and controlled for.

## Composition representation

```json
{
 "composition_id":"comp_synthetic_1",
 "match_id":"match_synthetic_1",
 "team_id":"team_blue",
 "patch":"synthetic-1",
 "map":"Ascent",
 "slots":[
  {"player_id":"p_a","character_agent_id":"jett","character_role":"Duelist"},
  {"player_id":"p_b","character_agent_id":"omen","character_role":"Controller"},
  {"player_id":"p_c","character_agent_id":"sova","character_role":"Initiator"},
  {"player_id":"p_d","character_agent_id":"killjoy","character_role":"Sentinel"},
  {"player_id":"p_e","character_agent_id":"kayo","character_role":"Initiator"}
 ],
 "is_synthetic":true
}
```

Composition has **(a)** agent-character multiset, **(b)** human player assignments, and **(c)** coordination context. Separate lineup identity from function/role distribution; official game-role labels can change by patch.

## Features for group composition analytics

- **Composition coverage:** number of observed rounds with lineup under chosen map and patch.
- **Human playstyle diversity:** entropy/spread of normalized style vectors within team, not character classes.
- **Behavior complementarity:** e.g. propensity of teammate utility before another player's entry (requires verified observations), matching aggressive entry with support, postplant hold coverage.
- **Relative spacing and trade conversion:** only when synchronized geometry or reliable event labels are available.
- **Coordination timing:** distribution of gaps `utility_time→engagement_time` and `death→trade_attempt`, plus missingness.
- **Behavior role-switch adaptation:** difference of same player's normalized feature vectors across picks and lineups; use uncertainty and common contexts.
- **Patch/map context:** lineup efficacy is not assumed to transfer across new patches or maps.
- **Team interaction network:** directed graph of observed support, trade, follow, or setup edges; counts and time windows, not guessed communications.

## Requested coach questions (authorized retrospective only)

- "Does the same player initiate early fights at a comparable rate while playing a Sentinel versus a Duelist in similar opportunities?"
- "Which players exhibit overlapping aggressive space-taking behavior despite selecting different agents?"
- "On Ascent defense, which observed composition produces more verified coordinated retakes in our own matches?"
- "Are two very similar human playstyles complementary or redundant in this composition?" Answer as a hypothesis with observed indicators, not win guarantees.
- "Show how the team's behavior changed after one player switched from Initiator to Controller." Show confounders and matched support.

## Composition outcome modeling (later, only with enough rights-cleared data)

Predict a conditional *outcome association* from a combination of player style vectors, agent picks, synergy features, map, side, patch and opponent aggregate context if permitted. Use match/team/time grouped held-out evaluation. Selection effects and opponent skill confounders mean a composition 'win lift' is **not causal** by default; do not state 'this comp adds +12% win chance' without rigorous calibration and uncertainty.

## Team role-flexibility visualization

Per player, display (i) normalized style centroid, (ii) spread by character role and specific pick, (iii) patch/time drift, (iv) top confidence intervals, (v) matched clips. Team page maps player–player similarity edges and ability/behavior interaction edges separately.

## StratSim — bounded research roadmap

**S0: decision explorer**: for a manually described and sufficiently supported game situation, return empirical distributions over a short allowed action taxonomy (hold, reposition, approach, utility, disengage). Source matched historical observations and intervals.

**S1: learned conditional action model**: fit calibrated classifier on events/states; report held-out macro-F1, negative log likelihood, Brier score, expected calibration error and coverage; compare with most-common-action and role-only baselines. Never output single 'certain' next action.

**S2: abstract team-level Monte Carlo**: state includes approximate map zone, alive counts, economy buckets, utility availability where observed, phase and objective state. Human style influences policy; a separately tested transition model supplies world dynamics. Multiple random seeds and counterfactual stress tests. **Not** a recreation of Riot game mechanics or a client mod. Avoid copying official maps/assets beyond permitted use. Disclose extrapolation and missing comms/reaction times.

**S3: pilot with real coach feedback**, only when simulation is externally validated. Never present these scenarios as exact reproductions of professional matches.

## Hard policy boundaries

Retrospective analysis and private self/team improvement with consent only. No pre-match identifiable opponent scouting in ordinary developer API product, no dynamic live-game instructions, no hidden-player identification, no game-client hooks. Any additional professional licensed workflow requires separately confirmed permission.
