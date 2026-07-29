# TRU Research Roadmap

Version: 1.1

Status: central prospective documentation.

This roadmap describes research direction and project maturity. It does not
validate scientific claims by itself. Hypotheses, formal definitions, and corpus
material require Project Owner validation before becoming normative TRU-AI
sources.

## Status Labels

- `integrated`: implemented in the codebase and covered by tests.
- `experimental`: available for exploration but not yet scientifically settled.
- `planned`: intended future work.
- `to validate`: requires Project Owner or scientific validation.
- `deferred`: intentionally postponed or not ready for integration.

## Current Software Baseline

Current active line: `0.9.6`.

Recently integrated capabilities:

- `9.2` Theory Evolution: `integrated`;
- `9.3` Prediction Engine: `integrated`;
- `9.4` Verification and Falsification: `integrated`.

Current scientific pipeline:

Observation
-> Theory Evolution
-> Prediction
-> Verification
-> Falsification
-> Scientific Gaps

Current demonstrator:

- `GET /scientific-demo`: `integrated`;
- `POST /reasoning/scientific-demo`: `integrated`;
- `GET /scientific/health`: `integrated`;
- `POST /scientific/analyze`: `integrated`.

Current quality baseline:

- full test suite: `514 passed`;
- Ruff: passing;
- mypy on `backend/tru_ai`: passing.

## 0.9.6 Focus

The `0.9.6` line stabilizes the integrated scientific pipeline as a generic
scientific API and keeps the historical demo compatible.

Recommended focus:

- keep the scientific demo aligned with the generic scientific service;
- preserve human-readable explanations derived from raw outputs;
- keep central documentation aligned with the release state;
- audit untracked corpus and formalization material separately;
- decide what belongs in Git and what remains generated or external.

## Integrated Research Capabilities

## Theory Evolution

Status: `integrated`.

The codebase tracks theory history, snapshots, and operator traces for
scientific reasoning.

Research caution: generated theory changes must remain tied to explicit models,
input data, and traceable execution results.

## Prediction

Status: `integrated`.

The codebase can generate scientific predictions, scenarios, simulations, and
confidence adjustments.

Research caution: predictions are not observations and must not be presented as
verification.

## Verification And Falsification

Status: `integrated`.

The codebase distinguishes verification outcomes and falsification results.

Research caution: `confirmed`, `contradicted`, `inconclusive`, and `not_tested`
states must stay explicit.

## Experimental Or To Validate

The following areas may be valuable but should not be treated as validated
scientific truth merely because draft documents exist:

- formal TRU specification: `to validate`;
- TRU ontology and language documents: `to validate`;
- meta-model formalization: `to validate`;
- observatory concept: `planned` and `to validate`;
- cognitive conversation corpus: `to validate`;
- request/response traces under `corpus/`: `to validate`.

Do not integrate corpus or formalization material automatically.

## Planned Research Directions

## Formalization

Status: `planned` and `to validate`.

Goal: decide which scientific definitions, language rules, ontology elements,
and meta-model claims are approved as project sources.

Validation needed:

- Project Owner review;
- consistency with implemented models;
- clear separation of hypotheses from established project definitions.

## Corpus Governance

Status: `planned` and `to validate`.

Goal: define how scientific and cognitive corpora are selected, anonymized,
stored, versioned, and used for tests or evaluation.

Validation needed:

- data sensitivity review;
- provenance review;
- criteria for generated versus curated data.

## Scientific Demonstration

Status: `integrated`, with future improvements `planned`.

Goal: keep `/scientific-demo` useful as a traceable demonstration of the
pipeline without turning demo outputs into scientific evidence.

Future work may include richer incomplete-case examples, better explanation
inspection, and clearer separation between raw outputs and readable summaries.

## Observatory

Status: `planned` and `to validate`.

Goal: explore whether an observation repository should exist and how it would be
validated.

No current untracked observatory document should become normative without
scientific review.

## Deferred Or Not Yet Ready

The following should remain deferred until explicitly approved:

- broad alpha tagging before the `0.9.6` release is marked;
- broad corpus integration;
- release documentation integration;
- normative scientific document integration;
- independent observatory operation.

The current recommendation is to tag `v0.9.6` after release validation, then
continue corpus and formalization decisions in separate lots.

## Research Integrity Rules

Research documentation must:

- identify hypotheses as hypotheses;
- avoid presenting simulations as observations;
- avoid presenting predictions as verification;
- preserve uncertainty;
- distinguish implemented software from validated science.

Every validated contradiction may improve the theory, but no automated process
should revise scientific principles without Project Owner instruction.
