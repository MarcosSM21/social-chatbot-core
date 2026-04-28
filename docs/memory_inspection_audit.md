# Memory Inspection Audit

This document audits the internal inspection tooling that already exists before Phase 25 introduces new improvements.

The goal is to answer:

- what memory inspection paths already exist
- what each one is good for
- what their limitations are
- which path should be improved first

## 1. Existing Inspection Paths

### A. Internal memory API endpoints

Already available in `app/api/main.py`:

- `GET /internal/memory/{platform}`
- `GET /internal/memory/{platform}/{external_user_id}`
- `DELETE /internal/memory/{platform}/{external_user_id}`
- `DELETE /internal/memory/empty`

What they are good for:

- inspect memory in application shape
- inspect one user or a platform list
- review structured memory fields without manually decoding DB JSON columns
- clean or reset memories when debugging

Strengths:

- already protected through internal API key
- already aligned with the selected memory backend through `build_user_memory_repository(settings)`
- already useful for structured memory inspection

Limitations:

- not especially optimized for SQLite-focused local debugging
- not yet designed as a compact “inspection view”
- not obviously centered on `working_memory_buffer` workflows

## 2. Prompt-level inspection script

Already available:

- `scripts/inspect_llm_prompt.py`

What it is good for:

- inspect what memory is actually being used on a turn
- inspect `retrieved_memory`
- inspect `retrieved_memory_reasons`
- inspect prompt composition

Strengths:

- very useful for debugging the final context sent to the model
- already shows:
  - `conversation_summary`
  - `stable_facts`
  - `preferences`
  - `relationship_notes`
  - `retrieved_memory`
  - `retrieved_memory_reasons`
  - `retrieval_strategy`
  - `working_memory_buffer`

Limitations:

- today it builds memory from `UserMemoryRepository(...)`
- that means it is JSON-oriented by default
- it does not automatically follow the configured repository/backend the way the internal API does

This is currently the clearest gap discovered in the audit.

## 3. Direct SQLite inspection

Already possible outside the app:

- DB Browser for SQLite
- DBeaver
- `sqlite3`

What it is good for:

- inspect the raw source of truth
- verify persistence directly
- debug repository-level storage

Strengths:

- most direct access to stored memory
- useful for verifying SQLite migration and repository behavior

Limitations:

- lower ergonomics than app-shaped inspection
- JSON columns are less pleasant to read manually
- not enough by itself for prompt/debug workflow

## 4. Current Coverage By Inspection Level

### Database level

Current status:

```text
good enough externally, but not yet ergonomically integrated into the project workflow
```

### Application level

Current status:

```text
already decent through internal memory endpoints
```

### Prompt level

Current status:

```text
useful, but not yet aligned with the configured memory backend
```

## 5. Most Important Finding

The internal API is already the strongest app-level inspection path.

The biggest inspection gap is not the absence of memory endpoints.

The biggest gap is:

```text
prompt inspection and repository/backend inspection are not yet fully aligned
```

In practice, this means:

- the app may use SQLite as its serious default backend
- but the prompt inspection script still reads memory through a JSON repository path

That weakens trust in prompt-level inspection.

## 6. Recommended Priority

The first tooling improvement should most likely be:

```text
make prompt inspection follow the configured memory backend, especially SQLite
```

Why this first:

- it closes the biggest current mismatch
- it improves trust in prompt inspection
- it connects storage-level truth with prompt-level behavior
- it stays aligned with the SQLite-first direction of the project

## 7. Secondary Improvements

After that, likely good next improvements are:

- a more explicit inspection-friendly internal memory view
- lightweight SQLite-oriented helper scripts
- easier filtering by platform/user/recently updated memories

## 8. Audit Conclusion

The project already has real inspection tooling.

This phase does not start from zero.

The current state is better described as:

```text
inspection exists, but the most important next step is to align prompt inspection with the actual configured memory backend
```
