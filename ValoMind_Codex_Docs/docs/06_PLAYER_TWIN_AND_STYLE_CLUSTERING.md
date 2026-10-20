# 06 — ValoTwin & StyleMap: Cross-Role Player Modeling (KEY DOCUMENT)

## Specific user requirement

**Group human players into meaningful behavioral categories based on how similarly they play even when they use different VALORANT characters, character roles, maps and five-character team compositions.** Do NOT simply compare Duelist to Duelist or group players by agent role, pick rate, ACS/KD, or fixed positions. The system must also explain when comparison is invalid because gameplay contexts do not overlap.

## Model mental model

For human player \(p\), observed behavior \(b\) is influenced by:

\[ b \approx f(\text{player style}_p,\;\text{VALORANT character},\;\text{team composition},\;\text{map},\;\text{side},\;\text{game state},\;\text{patch}) + \epsilon \]

We want a **player-level style representation** that generalizes across roles, while preserving contextual effects rather than pretending roles have no influence. In observational footage, full causal deconfounding is generally impossible; frame outputs as context-adjusted associations.

## Design: two parallel representations

1. **Intrinsic-ish normalized style vector** `style_base`: behavior conditional on eligible opportunities, adjusted for observed confounders. Useful for comparison **across** VALORANT character agents/roles.
2. **Context behavior vector** `style_context`: style conditioned on chosen agent/role, map, side, patch, 5-agent lineup, round phase, economy etc. Useful for same-player comparisons under different circumstances.

Never throw away context to achieve 'role independence'; store it separately, then normalize when enough overlap exists.

## Canonical per-opportunity feature families v1 (implement first 12)

| Feature | Operational numerator | Eligible denominator | Counterexamples / caveats |
|---|---|---|---|
| `first_contact_propensity` | first-contact attempts | rounds with verified contact chance | not all roles exposed to same chance |
| `early_map_space_attempt_rate` | early-round forward-zone entries | rounds with observed opening route | no game coordinates? use region tags |
| `repeek_after_contact_rate` | second peek within defined window | verified first contacts | avoid counting utility-forced peeks |
| `disengagement_rate` | exits duel after contact | documented first contacts | retreat may be correct play |
| `solo_path_rate` | independent route segments | synchronized teammate path samples | missing teammates→null |
| `late_rotation_commit_rate` | rotate after late cue | verified actionable rotation cues | cue availability differs by POV |
| `utility_before_contact_rate` | utility used before observed contact | observable eligible engagements | usage opportunities differ by kit |
| `utility_followup_rate` | utility leads a team action | verified utility + team action | do not equate different ability kits |
| `trade_attempt_propensity` | follow-up attempt within Δt | verifiable teammate deaths close enough | geometric calibration required for some cases |
| `postplant_anchor_rate` | hold rather than chase | observed postplant duties | positional duties differ |
| `save_vs_retake_choice_rate` | save or retake decision inferred from action | late-round relevant states | distinguish observed from assumed |
| `adaptation_after_loss_rate` | qualifying behavior change after lost round | comparable before/after contexts | minimum sample size essential |
| `site_entry_timing_median` | time to site entry | verified execution rounds | patch/map & round style confounded |
| `spacing_to_teammates` | relative teammate distance over time | calibrated synchronized position samples | null without ground truth |
| `risk_at_disadvantage` | assertive actions when player deficit | eligible disadvantage decisions | outcome-independent risk definition |
| `objective_priority_rate` | objective-oriented movement decisions | verified objective opportunity | human review of context |

Also retain raw opportunity counts, `missing_reason`, recording perspective, annotator agreement and sample size for every feature. Player role is not a feature used **directly** to define base similarity.

## Typed feature row

```json
{
  "player_id":"p_synthetic_a",
  "feature_recipe":"style_v1",
  "cohort":{"patches":["synthetic-1"],"maps":["Ascent"],"side":"attack"},
  "values":{"first_contact_propensity":0.71,"disengagement_rate":0.22,"utility_before_contact_rate":null},
  "opportunities":{"first_contact_propensity":42,"disengagement_rate":18,"utility_before_contact_rate":0},
  "masks":{"first_contact_propensity":true,"disengagement_rate":true,"utility_before_contact_rate":false},
  "context":{"character_picks":["Jett","Cypher"],"character_roles":["Duelist","Sentinel"],"team_compositions":["comp_1","comp_2"]},
  "annotation_quality":0.91,
  "model_version":"0.1.0",
  "is_synthetic":true
}
```

## Computation stages

### Stage A — Opportunity-normalized rates

Use \(\hat r = (k + \alpha)/(n+\alpha+\beta)\) for binary events with explicit eligible opportunity denominator \(n\); store posterior variance/credible interval or bootstrap intervals. Do not set feature to 0 when no observation. Require sample thresholds configurable per feature (pilot default 20 opportunities; not a universally validated threshold).

### Stage B — Context adjustment

For a feature \(j\), estimate baseline probability from comparable contexts \(\hat E[b_j|c]\), where \(c\) includes map, side, phase, patch, available known game state, character capability constraints and lineup. A simple interpretable first baseline is a stratified context mean with partial pooling. Residual \(r_{p,j} = E[b_{p,j} - \hat E[b_j|c]\mid p]\) estimates how that player differs from the **contextual norm**. Later use hierarchical/mixed effects or learned embeddings with domain-adversarial diagnostics.

**Overlap rule:** when comparing players A and B, compute only contexts where both have comparable eligible opportunities, or explicitly pool using a documented estimation procedure. If effective sample size, shared contexts or annotation coverage is insufficient, return `not_comparable` and explain why. Do not rely on arbitrary extrapolation from Jett entries to Sentinel anchor rounds.

### Stage C — Style vector and missingness

Use standardized residuals and eligible behavior statistics. Fit scalers **only on training partition**. Maintain feature masks and weights based on reliability, annotator agreement and confidence. Do not blindly impute missing observations with 0 or with the global mean without flags. For distance, compare observed shared dimensions and penalize small common coverage.

### Stage D — Distance + neighbor recommendations

Baseline weighted standardized distance:

\[ d(A,B) = \sqrt{\frac{\sum_{j\in J_{AB}} w_j (z_{Aj}-z_{Bj})^2}{\sum_{j\in J_{AB}} w_j}} \]

with \(J_{AB}\) features adequately observed in **both**. Return `distance`, `coverage`, `support`, `uncertainty`, and optional user-friendly similarity only after fitting a held-out/calibration mapping. **Do not convert distance into '87% similar' using an arbitrary exponential without labeling it as an uncalibrated UI score.**

### Stage E — Discover categories

Start with agglomerative clustering or HDBSCAN on reliable player vectors. Include noise/unassigned class; test cluster stability across bootstrap matches and temporal splits. Assign *descriptive* labels only after cluster centroids, high-impact dimensions and representative evidence are reviewed. A player may belong probabilistically to multiple categories or shift over patches; expose memberships and per-context variants.

Suggested **provisional** vocabulary (not labels to force onto data): proactive space-taker; calculated re-engager; patient information-gatherer; reactive map rotator; utility-first facilitator; objective-first stabilizer; flexible opportunist. Names describe behavior, not moral skill quality or character role.

### Stage F — Explain a similarity result

For players A (Jett) and B (Cypher), show (a) shared opportunities and what was excluded, (b) normalized top shared features, (c) five strong counterexamples, (d) context and lineup distribution, (e) time and annotation sample adequacy, (f) links to corroborating clips. Display partial overlap rather than overclaiming full personality match.

## Cross-role versus composition: explicit three-mode UX

1. **Behavior style (normalized):** "Who plays similarly irrespective of character agent role?" Context-adjusted cross-role comparability with masks.
2. **Context-matched:** "Who behaves similarly in the same map, side, round phase, economy and agent lineup?" Strict match/stratified comparison.
3. **Role/composition breakdown:** "How does this player change when switching Jett→Cypher or under double-controller comps?" Same-player conditional comparison; support and confounding caveats.

## Verification experiments for unbiased role-independent categories

- **Synthetic invariance test:** A = Duelist aggressive, B = Sentinel aggressive, C = Duelist passive. Assert `d(A,B) < d(A,C)` after context adjustment. Test persists after assigning agent picks swapped.
- **Composition sensitivity test:** changing team comp only changes context analysis and residual baseline, not raw observed events.
- **Ablation:** raw performance stats only vs behavior rates vs context-normalized style; test role leakage with probe classifier predicting selected agent role from base vector (lower predictability desirable but cannot erase useful behavior).
- **Unseen agent test:** hold out one character-agent pick per player where sample support allows; evaluate neighbor/category consistency and action prediction degradation.
- **Temporal stability:** bootstrap by match, split older/newer matches, measure adjusted Rand index/NMI (on comparable cohorts), neighbor overlap and label stability.
- **Annotation sensitivity:** inject plausible label error and track robust distance drift.
- **Fairness:** compare confidence and abstention rates across roles, maps, skill strata and character pick frequency; avoid small cohorts masquerading as neutral style.
- **Expert study:** blinded coaches rate whether nearest neighbors play similarly; compare with role-based and K/D baselines.

## Core API return semantics

`POST /api/v1/style/compare {player_a, player_b, filters, mode}` returns:

```json
{
 "status":"comparable",
 "mode":"role_normalized",
 "distance":0.48,
 "similarity_score":null,
 "calibrated":false,
 "coverage":{"shared_features":10,"possible_features":16,"shared_opportunities":36},
 "top_shared_dimensions":[{"name":"first_contact_propensity","a":0.61,"b":0.64,"evidence_ids":["ev1","ev2"]}],
 "key_differences":[{"name":"disengagement_rate","a":0.2,"b":0.36}],
 "context_warning":"Limited controller-lineup overlap; scores are observational.",
 "feature_version":"style_v1","style_model_version":"baseline_v1"
}
```

`status` can be `comparable`, `limited_overlap`, `not_comparable`, `insufficient_data`, `stale_model`. Never expose numeric score if unsupported.

## Do not build

No role-label shortcut clusters; no arbitrary 'brains like TenZ' mind-reading; no false true-twin claim; no 'role-free' comparisons without coverage; no ranking of player worth; no simultaneous use of evaluation and training matches; no fake percentage similarity.
