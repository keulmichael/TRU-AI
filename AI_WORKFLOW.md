# TRU-AI AI Development Workflow

Version: 1.1

Status: central operational documentation.

`CODEX.md` remains the permanent development manual and has priority over this
workflow. This document describes the practical sequence to follow during a
TRU-AI contribution.

## Purpose

The workflow keeps AI-assisted development reproducible, scoped, testable, and
scientifically cautious.

It applies to work performed by Codex, ChatGPT, or any other AI assistant on the
project.

## Roles

## Project Owner

The Project Owner owns:

- scientific direction;
- roadmap priorities;
- validation of scientific concepts;
- final acceptance of project changes.

Only the Project Owner can decide that a scientific concept becomes part of
TRU-AI.

## ChatGPT

ChatGPT may help with:

- architecture discussion;
- technical specifications;
- scientific consistency review;
- documentation drafting;
- release planning.

ChatGPT does not replace the Project Owner.

## Codex

Codex is the implementation agent. Codex may:

- inspect the repository;
- modify scoped project files;
- run tests and quality tools;
- prepare commits when requested;
- report the exact final state.

Codex must not invent scientific concepts, alter scientific principles, or push
changes without an explicit request.

## Source Of Truth

Git history is the source of truth for versioned project state.

Untracked files are not automatically part of the project. They must be audited,
classified, and intentionally integrated before they become source material.

`CODEX.md` is the source of truth for development rules. This workflow is
supporting operational documentation.

## Standard Work Cycle

## 1. Read Context

Before modification, read:

- `CODEX.md`;
- task-specific central documentation;
- directly relevant code and tests.

Read supplementary scientific documents only when the task directly concerns
their content.

## 2. Audit The Working Tree

Run and inspect:

```powershell
git status --short
git diff --stat
git diff --name-status
```

Identify:

- tracked modifications;
- untracked files;
- files unrelated to the task;
- files that may contain multiple functional lots.

Do not assume an untracked file belongs to the current task.

## 3. Define Scope

Before editing, decide:

- which files are in scope;
- which files are explicitly out of scope;
- which validations are required;
- whether scientific owner validation is required.

Do not mix code, corpus, release documentation, central documentation, and
generated artifacts in the same commit.

## 4. Reuse Architecture

Prefer existing modules and public interfaces.

For reasoning flows, reuse `ReasoningPlanner` and `ReasoningExecutor`. Do not
create a parallel reasoning engine.

Extend existing models and engines before adding new abstractions.

## 5. Implement

Make the smallest coherent change that satisfies the task.

Preserve:

- runtime behavior unless the task requires a change;
- model serialization;
- deterministic execution;
- explicit error handling;
- separation between raw results and human-readable explanations.

Do not persist data implicitly.

## 6. Run Targeted Tests

Run the tests closest to the modified behavior first.

If a targeted test fails, identify whether the failure is caused by the task,
pre-existing state, or the environment.

## 7. Run Full Validation

Standard validation:

```powershell
python -m pytest
python -m ruff check backend/tru_ai backend/tests backend/scripts
python -m mypy backend/tru_ai
git diff --check
```

`pytest`, Ruff, mypy, and `git diff --check` must be reported. New type errors
or lint failures introduced by a task must be fixed in scope.

## 8. Review The Diff

Before staging, inspect:

```powershell
git diff --stat
git diff --name-status
git status --short
```

Check that every modified file belongs to the task.

## 9. Stage Intentionally

Never use `git add .` without a prior audit.

Stage only the files that belong to the coherent functional lot.

Then inspect:

```powershell
git diff --cached --stat
git diff --cached --name-status
git diff --cached
git diff --cached --check
```

## 10. Commit

Create a commit only when:

- the staged diff contains only intended files;
- validations pass or known exceptions are explicitly reported;
- no unrelated work is included;
- no user work is lost.

Never rewrite history or remove user commits without explicit instruction.

## 11. Report

Final reports should include:

- commit hash, if created;
- files included and excluded;
- summary of changes;
- targeted and full validation results;
- remaining Git state;
- confirmation that no push was performed.

## Git And Push Policy

Commits should represent one coherent unit.

Do not push, create tags, create branches, rebase, or rewrite history unless the
user explicitly asks for that action.

## Scientific Integrity

Scientific claims must stay traceable to validated project sources or real
execution results.

Do not:

- turn a hypothesis into a fact;
- present a simulation as an observation;
- present a prediction as a verification;
- invent scientific stages, operators, or theory revisions.

Scientific uncertainty must remain explicit.

## Definition Of Done

A task is done only when:

- the requested scope is handled;
- architecture rules are respected;
- relevant validations have run;
- the diff has been reviewed;
- the final Git state is clear;
- no unrelated file, corpus, release note, or artifact was integrated.
