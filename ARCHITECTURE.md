# TRU-AI Architecture

Version: 1.1

Status: central descriptive documentation.

This document describes the architecture that exists in the repository. It does
not define scientific principles. `CODEX.md` remains the authority for
development rules, and validated scientific documents remain the authority for
scientific definitions.

## Architectural Intent

TRU-AI is a backend-centered scientific software platform. Its architecture
prioritizes:

- deterministic behavior;
- explicit data models;
- testable domain modules;
- traceable reasoning results;
- separation between code, corpus, and documentation.

## Repository Shape

The runtime implementation lives under `backend/tru_ai`.

Current top-level backend domains include:

- `api`: FastAPI entrypoint and HTTP routes;
- `cognitive`: cognitive workflows, static demo assets, and scientific
  reasoning;
- `exploration`: graph exploration queries, indexes, path finding, patterns,
  and validation;
- `graph`: graph construction and graph data models;
- `inference`: inference rules, matching, validation, and repositories;
- `memory`: source import and canonical memory construction;
- `query`: graph query repository and query execution support;
- `semantic`: semantic resolution and alias/candidate handling;
- `extraction`, `parsing`, `relations`, `retrieval`, `ontology`,
  `discovery`, `config`, and `utils`: supporting domain and infrastructure
  modules.

Do not document or build a new subsystem as present until it exists in the
repository.

## API Layer

`backend/tru_ai/api/main.py` exposes the application through FastAPI.

The current user-facing scientific demo uses:

- `GET /scientific-demo`;
- `POST /reasoning/scientific-demo`.

API handlers should keep transport concerns separate from cognitive and
reasoning logic.

## Static Demo Interface

Static cognitive assets live in `backend/tru_ai/cognitive/static`.

The scientific demo files are:

- `scientific-demo.html`;
- `scientific-demo.css`;
- `scientific-demo.js`.

Dynamic HTML content must be escaped. Human-readable explanations must be built
from real execution results while raw results remain available separately.

## Cognitive Domain

`backend/tru_ai/cognitive` contains higher-level cognitive workflows.

Important areas:

- `conversation`: conversation pipeline and follow-up handling;
- `reasoning`: planning, execution, policy, models, and engines;
- `static`: local HTML/CSS/JS interfaces.

The cognitive layer should orchestrate domain components without embedding
corpus data or hidden persistence.

## Reasoning Architecture

Scientific and cognitive reasoning are centered on:

- `ReasoningPlanner`;
- `ReasoningExecutor`;
- reasoning models in `backend/tru_ai/cognitive/reasoning/models.py`;
- policy decisions in `backend/tru_ai/cognitive/reasoning/policy.py`;
- engines in `backend/tru_ai/cognitive/reasoning/engines`.

Reasoning flows must reuse `ReasoningPlanner` and `ReasoningExecutor`. Do not
create a parallel reasoning engine for scientific stages.

## Scientific Pipeline

The integrated scientific pipeline order is:

Observation
-> Theory Evolution
-> Prediction
-> Verification
-> Falsification
-> Scientific Gaps

This order must not be changed without explicit instruction.

The current pipeline is backed by:

- observation handling;
- theory construction, comparison, and evolution;
- prediction scenario generation and simulation;
- verification against observations;
- falsification analysis;
- scientific gap reporting.

Relevant engines include `observation.py`, `scientific.py`,
`falsification.py`, and supporting reasoning engines.

## Reasoning Results

Reasoning results are structured models, not free-form text.

Important result concerns include:

- raw observations and extracted claims;
- theory history and operator traces;
- predictions, scenarios, and simulations;
- verification and falsification reports;
- final gaps and human-readable explanations.

Model changes must preserve serialization, avoid shared mutable defaults, and
update public exports when needed.

## Exploration Domain

`backend/tru_ai/exploration` supports graph exploration.

It contains query models, indexes, path finding, pattern matching, repository
access, and validators. Exploration should depend on graph and query data
through explicit models rather than ad hoc structures.

## Inference Domain

`backend/tru_ai/inference` contains inference rules, rule application, matching,
validation, and persistence helpers.

Inference code should keep source edges, inferred edges, rule metadata, and
validation reports explicit and serializable.

## Memory Domain

`backend/tru_ai/memory` builds canonical memory from imported source documents.

Memory construction should be explicit: no implicit corpus ingestion, no hidden
persistence, and no automatic integration of generated conversation data.

## Conversation Domain

`backend/tru_ai/cognitive/conversation` coordinates conversational state and
follow-up behavior.

Conversation handling may use reasoning outputs, but it should not redefine
scientific status, verification status, or falsification semantics.

## Corpus And Documentation Separation

Source code, corpus data, release documentation, formal scientific documents,
and generated artifacts are separate lots.

Do not integrate:

- `corpus/`;
- `formal/`;
- `docs/releases/`;
- lot-specific `README-*` files;
- textual test artifacts;

unless the task explicitly asks for that lot and the content has been audited.

## Dependency Rules

Prefer dependencies that flow from orchestration toward domain modules and
explicit models.

Avoid:

- circular imports;
- UI dependencies inside domain logic;
- persistence side effects inside pure reasoning;
- duplicated planners, executors, or engines.

## Testing Strategy

Architecture changes require targeted tests for the touched domain and then the
standard validation suite:

```powershell
python -m pytest
python -m ruff check backend/tru_ai backend/tests backend/scripts
python -m mypy backend/tru_ai
git diff --check
```

Correctness and scientific traceability have priority over performance.
