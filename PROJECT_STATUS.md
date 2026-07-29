# TRU-AI Project Status

Version: `1.0.0`

Status: stable local product baseline.

## Engine State

The generic scientific engine is available through a public API, a generic Web
workbench, and the historical scientific demo route.

Current pipeline:

Observation
-> Theory Evolution
-> Prediction
-> Verification
-> Falsification
-> Scientific Gaps

## Completed Components

- Public scientific input and output models.
- `ScientificInputAdapter`.
- `ScientificService` facade.
- `ScientificExplanationService`.
- Generic API routes: `GET /scientific/health` and `POST /scientific/analyze`.
- Generic static workbench: `GET /scientific`.
- Demo compatibility route: `POST /reasoning/scientific-demo`.
- Historical static demo page: `GET /scientific-demo`.
- Confirmatory, contradictory, and incomplete examples in the generic
  workbench.

## Deferred Components

- Scientific sessions.
- Persistence for scientific analyses.
- Corpus ingestion through the scientific API.
- External scientific validation.
- Exports.
- Authentication and administration.
- Product dashboard.
- Autonomous learning.

## Last Validation

- Full test suite: `521 passed`.
- Ruff: passing.
- mypy: passing on `backend/tru_ai`.
- `git diff --check`: passing.

## Next Version Objective

The next version should be scoped after user feedback on the 1.0 workbench.
Deferred capabilities must be designed and validated separately before
implementation.

## Known Risks

- Scientific corpus and formalization documents still require owner validation
  before integration.
- The generic engine is deterministic and local, but it does not perform
  external scientific validation.
- No implicit persistence exists; callers must not assume analysis history is
  stored.
