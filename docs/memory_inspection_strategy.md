# Memory Inspection Strategy

This document defines the recommended way to inspect memory during Phase 25.

Its goal is to make memory easier to understand, review, and debug now that the project already includes:

- persistent structured memory
- `conversation_summary`
- `working_memory_buffer`
- turn-level memory retrieval
- multiple storage paths and a SQLite-first direction

## 1. Why Inspection Matters

Memory is no longer a small side feature.

The project now contains several memory layers and multiple update rules, so inspection is required to answer practical questions such as:

- what memory does this user currently have
- what is in `stable_facts`
- what is in `preferences`
- what is in `conversation_summary`
- what is in `working_memory_buffer`
- when was memory last updated
- whether memory behavior matches the intended policy

If memory cannot be inspected easily, it becomes much harder to trust.

## 2. Primary Storage Direction

The project now treats SQLite as the serious default backend for memory.

That means the main inspection strategy should focus on:

```text
SQLite first
```

JSON files can still be useful in some simple or legacy flows, but Phase 25 should assume that long-term inspection should work well with the SQLite memory repository.

## 3. Recommended Inspection Layers

Inspection should exist at more than one level.

### Layer 1: direct database inspection

Purpose:

- inspect raw stored state
- verify persistence
- debug repository behavior

Recommended tools:

- DB Browser for SQLite
- DBeaver
- `sqlite3` CLI

This is the most direct source of truth.

### Layer 2: internal application inspection

Purpose:

- inspect memory in application shape
- avoid manually decoding JSON columns
- verify what the app exposes, not only what the DB stores

Recommended candidates:

- internal API memory endpoints
- lightweight CLI inspection scripts

This layer is often better for day-to-day debugging.

### Layer 3: prompt-level inspection

Purpose:

- understand what memory is actually being used on a turn
- verify `retrieved_memory`
- verify `retrieved_memory_reasons`
- understand prompt composition

Current project support already includes prompt inspection through:

- `scripts/inspect_llm_prompt.py`

This is not a replacement for storage inspection, but it is essential for debugging memory usage.

## 4. What Must Be Easy To Inspect

By the end of this phase, it should be easy to inspect at least:

- `platform`
- `external_user_id`
- `last_known_username`
- `last_seen_at`
- `updated_at`
- `stable_facts`
- `preferences`
- `relationship_notes`
- `conversation_summary`
- `working_memory_buffer`

If these fields are not easy to inspect, the memory system remains too opaque.

## 5. Practical Tooling Direction

Phase 25 should avoid overengineering.

The goal is not to build a large admin panel immediately.

The preferred order is:

1. make SQLite inspection practical
2. improve internal inspection ergonomics
3. only later consider richer UI or more advanced tooling

That means the most realistic direction is likely:

- document recommended SQLite tools
- improve internal endpoints or scripts
- keep the workflow lightweight and local-first

## 6. Recommended Human Workflow

The intended debugging workflow should gradually become:

1. inspect stored memory in SQLite
2. inspect app-shaped memory through API or script
3. inspect prompt-level retrieved memory for a turn
4. compare:
   - what is stored
   - what is selected
   - what is actually sent to the model

This comparison is the key to debugging memory behavior well.

## 7. Phase 25 Design Goal

The design goal is not:

```text
add more memory logic
```

The design goal is:

```text
make existing memory visible enough to reason about confidently
```

## 8. One-Line Rule

```text
Phase 25 should make memory easy to inspect at the database, application, and prompt levels without requiring constant manual code reading
```
