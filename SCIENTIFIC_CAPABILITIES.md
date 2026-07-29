# TRU-AI Scientific Capabilities

Version: `0.9.6`

This document describes only capabilities implemented in the repository.

## Objective

The scientific engine provides a reusable API for running the existing TRU-AI
scientific reasoning pipeline against user-supplied scientific inputs.

## Public Inputs

`POST /scientific/analyze` accepts `ScientificAnalysisRequest`.

Supported input fields include:

- `question`;
- `intent`, defaulting to `scientific_research`;
- `theory_version`;
- `theory`;
- `baseline_theory`;
- `theory_history`;
- `comparison_theories`;
- `predictions`;
- `prediction_rules`;
- `scenarios`;
- `scientific_observations`;
- `options`.

Options currently include:

- `include_raw_result`;
- `include_human_readable`;
- `persist`.

`persist` defaults to `false` and does not trigger persistence in `0.9.6`.

## Pipeline

The available pipeline is:

Observation
-> Theory Evolution
-> Prediction
-> Verification
-> Falsification
-> Scientific Gaps

## Outputs

`ScientificAnalysisResult` can expose:

- `analysis_id`;
- `execution_plan`;
- `summary`;
- `human_readable`;
- `stage_cards`;
- `operator_trace`;
- `theory_graph`;
- `theory_evolution`;
- `theory_history`;
- `scientific_predictions`;
- `scientific_scenarios`;
- `scenario_simulations`;
- `scientific_observations`;
- `verification_reports`;
- `falsification_reports`;
- revision recommendations;
- `scientific_gaps`;
- optional `raw_result`.

Revision recommendations are not applied mutations.

## Public Architecture

The public scientific layer is composed of:

- `ScientificAnalysisRequest`;
- `ScientificInputAdapter`;
- `ScientificService`;
- `ScientificExplanationService`;
- `ScientificAnalysisResult`;
- `backend/tru_ai/scientific/api.py`.

`ScientificService` reuses the existing `ReasoningPlanner` and
`ReasoningExecutor`. No parallel scientific engine exists.

## Routes

- `GET /scientific/health`
- `POST /scientific/analyze`
- `GET /scientific-demo`
- `POST /reasoning/scientific-demo`

The `/reasoning/scientific-demo` route is a compatibility wrapper around the
generic scientific service.

## Guarantees

- No implicit persistence.
- No automatic corpus ingestion.
- Raw results are kept separate from human-readable projections.
- Human-readable projections are derived from actual execution results.
- The historical scientific demo remains compatible.

## Current Limits

- No scientific sessions.
- No stored analysis history.
- No import of user documents.
- No dynamic corpus ingestion.
- No external scientific validation.
- No export format.
- No authentication or administration layer for the scientific API.
- No autonomous learning.

## Minimal API Call

```bash
curl -X POST http://127.0.0.1:8000/scientific/analyze \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"Analyze this scientific observation.\"}"
```
