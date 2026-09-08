# Developer 1 Implementation Guide

This document is the implementation handoff for Developer 1's complete **HOW TO
ADVISE** responsibility in the v3.0 conception baseline. Agricultural meaning,
thresholds, sources, terminology, and validation remain Developer 2's responsibility.

## Component-to-file map

| Conception component | Implementation | Main responsibility |
| --- | --- | --- |
| AdvisoryEngine | `engine/advisory/engine.py` | Executes and traces the complete pipeline |
| CropTreeSelector | `engine/advisory/selector.py` | Starts at T1 and expands T2-T7 dynamically |
| RuleEvaluator | `engine/advisory/evaluator.py` | Evaluates declarative conditions and records evidence |
| ConstraintProcessor | `engine/advisory/constraints.py` | Applies validated hard exclusions and soft penalties |
| ScoringStrategy | `engine/advisory/scoring.py` | MobileScore and SMSPriority component calculations |
| Ranker | `engine/advisory/ranking.py` | Stable candidate ordering |
| ConflictResolver | `engine/advisory/conflict.py` | Selects one winner per conflict group and records losers |
| RecommendationBuilder | `engine/advisory/recommendation.py` | Produces the canonical result or a cautious fallback |
| TraceRecorder | `engine/models/repositories.py` | Records decision evidence behind a replaceable interface |

All paths are relative to the repository root and match Section 14. Developer 1's
reasoning code is under `engine/advisory/`; shared contracts stay under
`engine/models/` and `engine/interfaces/`.

## Pipeline algorithm

`AdvisoryEngine.advise()` enforces this order:

1. Open or locate the Crop Passport by `(farmer_id, crop_id, plot_ref)`.
2. Build `AgriculturalContext` around the crop.
3. Select the first tree set; T1 is always first.
4. Retrieve matching crop/tree rules through `KnowledgeProvider`.
5. Evaluate every new rule exactly once.
6. Collect `requires_trees` from matched rules and expand until stable.
7. Apply constraints to matched candidates.
8. Choose MobileScore for Mobile/Voice, SMSPriority for SMS.
9. Rank candidates deterministically.
10. Resolve conflicting candidates by conflict group.
11. Build a canonical recommendation.
12. Create and store a complete `TraceRecord`.
13. Store the recommendation and update Passport/history.

The expansion loop is bounded by the seven-value `TreeId` enum. A rule can request
another tree but cannot execute Python or introduce an arbitrary tree name.

## Crop-first context

`CropContextBuilder` constructs these mandatory dimensions:

- `past`: only history for the target `crop_id` or its rotation family, plus the
  current Crop Passport when present;
- `present`: question/objective, stage, farmer soil/topography/weather evidence,
  observations, practices, and optional image references;
- `future`: supplied future evidence, cultivation period, and provider forecast;
- `uncertainty`: explicit provider failures or absent current/forecast information.

Farmer weather evidence is retained if an external provider fails. No provider value
is fabricated. The resulting warning is copied into both the recommendation and trace.

## Rule condition language

Rules are JSON and validate into `engine.models.domain.Rule`. Each condition contains:

```json
{
  "field": "present.weather.rainfall_class",
  "operator": "eq",
  "value": "heavy"
}
```

`field` is a safe dotted lookup into `AgriculturalContext`; it is never evaluated as
Python. Supported operators:

| Operator | Meaning |
| --- | --- |
| `eq`, `ne` | Equality / inequality |
| `gt`, `gte`, `lt`, `lte` | Ordered comparison |
| `in`, `not_in` | Actual scalar is/is not in the rule's collection |
| `contains` | Actual sequence/mapping contains the rule value |
| `exists`, `not_exists` | Field presence check; no `value` required |
| `between` | Inclusive lower and upper boundaries |

`condition_mode` is `all` by default or `any`.

Outcomes:

- `matched`: create the rule's candidate;
- `not_matched`: evidence exists but does not satisfy the rule;
- `insufficient_evidence`: required evidence is absent and no present condition
  conclusively fails the rule.

Every comparison records field, operator, expected value, actual value, match result,
and missing state.

## Constraint governance

A candidate can define constraints in knowledge data.

Hard examples:

```json
{
  "constraint_id": "crop.example.block-condition",
  "kind": "hard",
  "effect": "exclude_if",
  "condition": {"field": "present.example", "operator": "eq", "value": true},
  "reason": "Validated agronomic reason"
}
```

Soft example:

```json
{
  "constraint_id": "crop.example.soft-risk",
  "kind": "soft",
  "effect": "penalize_if",
  "condition": {"field": "present.example", "operator": "eq", "value": true},
  "reason": "Sourced soft factor",
  "penalty": 1.5
}
```

Rules enforce these invariants at load time:

- hard constraints use only `exclude_if` or `require`;
- soft constraints use only `penalize_if` and a positive penalty;
- hard constraints are accepted only on `validated` rules (`test_only` is allowed in
  tests);
- validated rules and profiles require `source.validated_by`.

No user preference or score can restore a hard-excluded candidate.

## Scoring

The engine implements the component names in Sections 10.1 and 10.2 of the book.
Agricultural component values come from Developer 2 rules; the engine supplies no
crop-specific value.

Mobile:

```text
crop_fit + soil_fit + soil_improvement_potential + topography_fit
+ weather_fit + regional_risk_fit + timing_fit + practice_fit
+ relevant_history_fit - risk_penalties - triggered_soft_penalties
```

SMS:

```text
weather_change_urgency + cultivation_period_relevance + regional_risk
+ soil_crop_relevance + practice_relevance + future_risk
- risk_penalties - triggered_soft_penalties
```

Default weights are neutral (`1.0`) because exact weights remain an open agricultural
decision. Inject a mapping when constructing `MobileScoringStrategy` or
`SMSPriorityScoringStrategy` after Developer 2 validation. Unknown/channel-inapplicable
components are ignored by that strategy and cannot leak Mobile scoring into SMS.

Scores are raw explainable totals, not probabilities. Do not label them confidence.

## Ranking and conflicts

Ranking order is deterministic:

1. descending total score;
2. descending rule priority;
3. ascending stable `candidate_id`.

Candidates that represent mutually exclusive conclusions share `conflict_group`.
The first ranked item wins; the resolver retains all losers, priorities, and the
selection rule in `ConflictRecord`. Compatible candidates are retained so one result
can cover soil action, timing, practice, and risk together.

## Recommendation behavior

The canonical contract contains:

```text
recommendation_id, request_id, crop_id, channel, primary, alternatives,
reasons, warnings, actions, selected_trees, rule_references,
score_breakdown, trace_id, uncertainty, created_at
```

When no candidate survives, `RecommendationBuilder` returns
`insufficient_evidence`; it never invents a threshold. Draft/test knowledge adds a
visible Developer 2 validation warning.

Mobile, SMS, and Voice formatters consume the canonical result only after it is
stored. SMS truncation occurs at a word boundary and never changes the trace.

## Trace completeness

Every `TraceRecord` stores:

- request/crop/channel identifiers;
- complete Context and crop-filtered Past/Present/Future dimensions;
- selected trees;
- all evaluated rules, including nonmatches and missing fields;
- constraint decisions;
- score contributions;
- ranked candidate IDs;
- conflict winner/losers;
- final recommendation, reasons, warnings, and actions;
- start/completion timestamps.

Trace contents may include farmer data. The current store is in-memory; a production
adapter must enforce authentication, authorization, encryption, and retention policy.

## Shared integration boundaries

Protocols in `engine/interfaces/providers.py` allow replacement without touching the engine:

- `CropProvider` / `KnowledgeProvider`
- `WeatherProvider`
- `HistoryProvider`
- `TranslationProvider` / `SpeechProvider`
- `SMSProvider`
- `TraceRecorder`
- `RecommendationRepository`
- `CropPassportRepository`

The composition root is `engine/bootstrap.py`. Replace an adapter there or in a
deployment-specific composition module; do not import vendor SDKs into engine code.

## V2 extension points

The conception book assigns these future components to Developer 1:

- `NotificationEngine`
- `DiseaseDetectionService`
- `ExpertEscalationService`

They are deliberately not activated in V1. Implement them as consumers of the same
`KnowledgeProvider`, `CropProvider`, `RecommendationBuilder`, and trace contracts.
Image classification output must be evidence, not a direct untraceable decision.

## Developer 1 completion checklist

- [x] No crop threshold in Python.
- [x] T1 is always the root.
- [x] Tree expansion terminates and is traceable.
- [x] Missing evidence is distinct from negative evidence.
- [x] Hard constraints cannot be overridden by scores.
- [x] Channel scoring is isolated.
- [x] Ranking is deterministic.
- [x] Conflicts retain decision evidence.
- [x] Empty evidence yields caution, not false certainty.
- [x] Past/Present/Future appear in every trace.
- [x] Provider failure is explicit.
- [x] Canonical output precedes formatting/delivery.
- [x] Mobile and SMS use one reasoning engine.
- [x] Crop Passport updates on request.
- [x] Tests cover unit, rule, integration, scenario, channel, and trace layers.
