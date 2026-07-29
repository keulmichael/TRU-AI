# Changelog

## [1.0.0]

- promoted the generic scientific engine to the first usable local product
  baseline;
- added `GET /scientific` as a generic Web workbench for
  `POST /scientific/analyze`;
- added confirmatory, contradictory, and incomplete examples to the workbench;
- kept the historical `GET /scientific-demo` and
  `POST /reasoning/scientific-demo` compatibility flow;
- kept `ScientificService` as the single scientific application facade for the
  generic API and demo compatibility route;
- kept persistence absent and disabled.

## [0.9.6]

- added public scientific analysis models for generic scientific requests and
  results;
- added `ScientificInputAdapter` to isolate mapping from public inputs to
  reasoning context;
- added `ScientificService` as the application facade over `ReasoningPlanner`
  and `ReasoningExecutor`;
- added `ScientificExplanationService` for reusable summaries, stage cards, and
  human-readable projections derived from real results;
- exposed `GET /scientific/health` and `POST /scientific/analyze`;
- migrated `POST /reasoning/scientific-demo` to the generic scientific service
  while preserving the historical response contract;
- preserved compatibility with `GET /scientific-demo`;
- kept scientific revisions as recommendations, not applied mutations;
- kept persistence disabled and absent from the scientific API.

## [0.9.5-dev]

- prepared the previous `0.9.5-dev` development line;
- added a single Python package version source for the package, CLI, and
  FastAPI metadata;
- cleaned generated artifact tracking.

## [0.9.4]

- added `ScientificObservation`, `VerificationReport`, and
  `FalsificationReport`;
- added `VerificationOperator` and `FalsificationOperator` to the cognitive
  pipeline;
- compared predictions explicitly against observations;
- produced scientific revisions as recommendations;
- kept serialization and operator traceability.

## [0.9.3]

- added deterministic prediction confidence;
- added normalized confidence levels;
- supported expected observations, horizons, and hypotheses;
- generated predictions from explicit conditional rules;
- added scientific scenarios and simulations.
