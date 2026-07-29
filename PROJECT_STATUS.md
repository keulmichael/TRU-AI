# TRU-AI Project Status

Version: `0.9.6`

Status: stable release candidate.

## Engine State

The generic scientific engine is available through the public scientific API and
the historical scientific demo route.

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
- Demo compatibility route: `POST /reasoning/scientific-demo`.
- Static demo page: `GET /scientific-demo`.

## Deferred Components

- Scientific sessions.
- Persistence for scientific analyses.
- Corpus ingestion through the scientific API.
- External scientific validation.
- Exports.
- Authentication and administration.
- Product dashboard.

## Last Validation

- Full test suite: `514 passed`.
- Ruff: passing.
- mypy: passing on `backend/tru_ai`.
- `git diff --check`: passing.

## Next Version Objective

The next version should focus on release tagging and then on explicitly scoped
post-release capabilities. No deferred component should be added without a
separate design and implementation lot.

## Known Risks

- Scientific corpus and formalization documents still require owner validation
  before integration.
- The generic engine is deterministic and local, but it does not perform
  external scientific validation.
- No implicit persistence exists; callers must not assume analysis history is
  stored.
