# Conception Book Traceability

Source: *Crop-Centered Agricultural Advisory System - System Architecture &
Conception Document v3.0*. The original PDF is included under `docs/reference/`.

## Section 14 repository alignment

| Conception-book area | Repository path | Responsibility |
| --- | --- | --- |
| Advisory engine | `engine/advisory/` | Developer 1 |
| Shared models and interfaces | `engine/models/`, `engine/interfaces/` | Shared |
| Crop forest | `knowledge/crops`, `soils`, `regional`, `topography`, `climate`, `timing`, `practices`, `risks`, `rules` | Developer 2 |
| External adapters | `integrations/weather`, `translation`, `speech`, `sms/simulator` | Shared |
| Language resources | `languages/` | Shared |
| Mobile/SMS backend routes | `api/mobile.py`, `api/sms.py` | Shared |
| Four test layers | `tests/engine`, `rules`, `integrations`, `scenarios` | Shared |

`scripts/check_structure.py` enforces these paths and rejects the former
`src/agricultural_advisory/` and `knowledge/demo/` layouts.

## Functional requirements

| ID | Implementation evidence |
| --- | --- |
| FR-01 | `CropContextBuilder`; `AdvisoryRequest` normalized around `crop_id` |
| FR-02 | `MobileAdvisoryRequest` accepts crop, question, characteristics, image references |
| FR-03 | `SMSAdvisoryRequest`, SMSPriority, formatter, simulator/inbox |
| FR-04 | crop/family-filtered request and stored history |
| FR-05 | `AgriculturalContext.present` plus rule evidence |
| FR-06 | `AgriculturalContext.future`, forecast adapter, timing rules |
| FR-07 | `CropTreeSelector.select/expand`; T1 invariant |
| FR-08 | `JSONKnowledgeProvider` + `RuleEvaluator` |
| FR-09 | constraints, channel scoring, ranker, conflict resolver |
| FR-10 | canonical primary/alternatives/reasons/warnings/actions; T2 action support |
| FR-11 | `TraceRecord` + recorder/retrieval endpoint |
| FR-12 | translation/TTS interfaces and post-reasoning adapters; TTS provider pending |
| FR-13 | Mobile/SMS/Voice formatters from one canonical result |
| FR-14 | crop provider/API supports education content integration; content belongs to Developer 2/frontend |
| FR-15 | tree contracts plus weather/history/context fields |
| FR-16 | rule status/version/source/validator contracts and validator script |

## Non-functional requirements

| Requirement | Evidence / production note |
| --- | --- |
| Explainable/auditable | Condition evidence, score breakdown, constraints, conflicts, trace |
| Knowledge changes without engine rewrite | JSON provider and declarative rule DSL |
| Replaceable external providers | Protocols and composition root |
| Multi-layer testing | `tests/engine`, `rules`, `integrations`, `scenarios` |
| Secure transport | Deployment must terminate HTTPS; Docker/API do not claim TLS termination |
| Controlled access | Authentication/RBAC remains an explicitly documented open production decision |
| Graceful provider failure | Weather failure becomes uncertainty; no fabricated values |
| Extensibility | Generic context/rules/providers, V2/V3/V4 interfaces preserved |

## Required API catalogue

| Book endpoint | Implemented route |
| --- | --- |
| `POST /api/v1/advisory/mobile` | `api/mobile.py` |
| `POST /api/v1/advisory/sms` | `api/sms.py` |
| `GET /api/v1/recommendations/{id}` | `api/system.py` |
| `GET /api/v1/crops` | `api/system.py` |
| `GET /api/v1/crops/{crop_id}` | `api/system.py` |
| `POST /api/v1/sms/simulate` | `api/sms.py` |
| `GET /api/v1/health` | `api/system.py` |
| `GET /api/v1/knowledge/version` | `api/system.py` |

An additional `GET /api/v1/sms/inbox/{recipient_id}` route exposes the book's virtual
inbox for development and tests.

## Domain entities

| Book entity | Implementation |
| --- | --- |
| Farmer | identifiers in request/context; authentication profile is future persistence work |
| Crop | `CropProfile` |
| CropPassport | `CropPassport` and `CropPassportService` |
| AdvisoryRequest | channel request models + normalized `AdvisoryRequest` |
| Context | `AgriculturalContext` |
| Rule | `Rule`, `Condition`, `ConstraintSpec` |
| RuleEvaluation | `RuleEvaluation`, `ConditionEvidence` |
| Recommendation | `Recommendation` |
| RecommendationItem | `Candidate`, `ScoredCandidate`, `CanonicalRecommendationItem` |
| Trace | `TraceRecord` |

## Acceptance baseline

| Baseline statement | Status |
| --- | --- |
| Python advisory engine | Implemented |
| Flutter client | External to this backend work; OpenAPI contract provided |
| V1 no IoT | Respected; no sensor dependency |
| Rule forest, not ML random forest | Respected |
| Seven trees re-rooted on T1 | Implemented and tested |
| Mobile target crop/question/evidence | Implemented |
| Proactive app-free SMS | Implemented with simulator |
| Shared reasoning, different scoring/presentation | Implemented and tested |
| Past/Present/Future mandatory | Implemented in Context and Trace |
| Trace every recommendation | Implemented and retrieval-tested |
| External providers isolated | Implemented |
| Developer 1 HOW / Developer 2 WHAT | Enforced in repository and validation model |
| Education and Voice retained | Provider/formatter boundaries retained; frontend/content pending |

## Intentional V1 deployment choices

The book leaves framework, database, cloud, and providers open. This implementation
selects FastAPI/Pydantic/Uvicorn for the Python modular monolith and in-memory stores
for a runnable V1 baseline. It does not choose a production database, auth provider,
cloud, SMS gateway, translation service, or TTS service on the user's behalf.

The adapters/protocols make those later choices replaceable without changing the
Developer 1 inference algorithm.
