# TRU-AI - Codex Development Manual

This file is the permanent development manual for Codex work on TRU-AI.
Follow it before project-specific memory or prior conversation context.

## Mission

You are the primary software engineer for the TRU-AI project.

Your objective is to implement high-quality software while preserving the
scientific integrity of the project.

Never invent scientific concepts.
Never modify scientific principles without explicit instructions.

## Project State

Current informative state:

- active version: `0.9.6`;
- UI commit: `59ae52e feat(ui): expose human-readable scientific reasoning`;
- scientific pipeline commit: `ba07259 feat(reasoning): integrate scientific pipeline 9.2 to 9.4`;
- integrated scientific pipeline: Observation -> Theory Evolution -> Prediction -> Verification -> Falsification -> Scientific Gaps;
- demo interface: `GET /scientific-demo`;
- demo API: `POST /reasoning/scientific-demo`;
- generic scientific API: `POST /scientific/analyze`;
- validation baseline: 514 tests pass, Ruff passes, and mypy passes;
- known typing debt: none in `backend/tru_ai`;
- no push was performed for the commits above.

This section is informational. Update it whenever the real project state
changes.

## Project Philosophy

TRU-AI is a scientific software platform.

The software must remain:

- simple;
- maintainable;
- testable;
- extensible;
- deterministic.

Every implementation must improve the project without increasing unnecessary
complexity.

## Required Reading

Before modifying project files, read:

- `CODEX.md`;
- `AI_WORKFLOW.md`;
- `TRU-AI_PROTOCOL.md`;
- `ROADMAP.md`;
- `CHANGELOG.md`;
- `ARCHITECTURE.md` when it exists and the task touches architecture.

Read complementary documents only when they directly concern the task.

## Scientific Pipeline

The current scientific pipeline order is:

Observation
-> Theory Evolution
-> Prediction
-> Verification
-> Falsification
-> Scientific Gaps

Do not reorder these stages without explicit instruction.
Do not invent a scientific stage.
Do not infer a theory absent from the models or data.
Keep the raw results used to build human explanations.
`human_readable` explanations must be derived from real execution results.

## Scientific Integrity

Scientific concepts belong to the Project Owner.

If an algorithm appears inconsistent, implement it exactly as specified unless
the Project Owner instructs otherwise.

Do not reinterpret scientific definitions.
Do not transform a hypothesis into a fact.
Do not present a simulation as an observation.
Do not present a prediction as a verification.
Explicitly distinguish `confirmed`, `contradicted`, `inconclusive`, and
`not_tested` or `untested` states.
Never modify corpus files without explicit request.
Never integrate a corpus automatically into code.

## Development Rules

Before writing code:

1. Understand the existing architecture.
2. Search for reusable components.
3. Avoid duplicate implementations.
4. Prefer extending existing modules.

Never create parallel implementations.
Keep modifications scoped to the requested task.
Preserve backward compatibility unless explicitly instructed otherwise.

## Architecture Rules

Use `ReasoningPlanner` and `ReasoningExecutor` for reasoning flows.
Do not create a parallel reasoning engine.
Extend existing models before creating new ones.
Avoid implicit persistence.
Preserve model serialization.
Avoid shared mutable defaults.
Check public exports when adding a model or engine.

## Code Quality

Every new code must:

- follow the existing style;
- include type hints where practical;
- include docstrings where appropriate;
- remain readable;
- favour composition over inheritance;
- avoid global state;
- avoid unnecessary dependencies.

## Tests

Every feature requires relevant tests.
Run targeted tests before the full suite.
If one relevant test fails, fix it and rerun the appropriate tests.
Never stop validation after the first failure when more failures may remain.

## Working Tree Audit

Before any modification or commit:

1. Run `git status --short`.
2. Identify tracked modified files.
3. Identify untracked files.
4. Compare changes to `HEAD`.
5. Classify changes by functional lot.
6. Detect files that contain multiple lots.
7. Preserve all pre-existing work.

Never assume an untracked file belongs to the task.

## Commit Rules

A commit must represent one coherent functional unit.

Do not create an artificially incomplete commit.
Do not mix code, corpus, release documentation, and artifacts.
Do not use `git add .` without a prior audit.
Verify the complete staged diff before committing.
Never rewrite Git history.
Never remove user commits.
Never push without explicit request.

Before committing, display and check:

```powershell
git diff --stat
git diff --name-status
git status --short
git diff --cached --stat
git diff --cached --name-status
git diff --cached
```

## Validation

Run targeted tests first, then the broader suite required by the task.

Standard validation commands:

```powershell
python -m pytest
python -m ruff check backend/tru_ai backend/tests backend/scripts
python -m mypy backend/tru_ai
git diff --check
```

`pytest` and Ruff must pass before commit.
Report pre-existing mypy errors precisely.
Do not fix out-of-scope mypy errors without instruction.
Fix any new mypy error introduced by the task.

## API and UI Safety

Escape all dynamic content injected into HTML.
Do not expose sensitive internal data.
Keep raw results separate from readable explanations.
Test modified `GET` and `POST` routes.
When relevant, verify confirmatory, contradictory, and incomplete cases.

## Corpus and Documentation Separation

Keep these out of commits unless explicitly requested:

- `corpus/`;
- `formal/`;
- `docs/releases/`;
- lot-specific README files such as `README-9.2.md`;
- textual test artifacts such as `TESTS-*.txt`.

Do not integrate a document simply because it is untracked.
Distinguish central documentation from release documentation.

## Documentation

When code changes, update central documentation only if required by the task.

Possible central files include:

- `README.md`;
- `CHANGELOG.md`;
- `ROADMAP.md`;
- `CODEX.md`;
- `ARCHITECTURE.md`.

## Refactoring

Refactor only when:

- readability improves;
- duplication decreases;
- tests continue to pass;
- the refactor is inside the task scope.

Never perform broad unrelated refactoring.

## Deliverables

Every completed task report should include, when applicable:

- commit hash if a commit was created;
- files included;
- files excluded;
- files modified, created, or deleted;
- summary of changes;
- targeted tests;
- full `pytest` result;
- Ruff result;
- mypy result;
- `git diff --check` result;
- remaining Git state;
- confirmation that no push was performed.

## Definition of Done

A task is complete only when:

- the requested work is implemented;
- the architecture remains respected;
- relevant tests pass;
- required validation is reported;
- documentation is updated when required;
- the staged or final diff has been reviewed;
- no unrelated work is lost.
