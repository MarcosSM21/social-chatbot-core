# SQLite Memory Visual Inspection

This document defines the practical visual inspection path for SQLite memory during Phase 25.

Its purpose is simple:

```text
open the database, inspect memory visually, and understand what is stored without needing to read code
```

## 1. Recommended Tools

Recommended visual tools:

- DB Browser for SQLite
- DBeaver

Recommended default choice:

```text
DB Browser for SQLite
```

Reason:

- lightweight
- visual
- easy to use locally
- enough for the current phase

## 2. Database Path

By default, the project uses:

```text
data/social_chatbot.sqlite3
```

This comes from:

```text
SQLITE_DATABASE_PATH
```

If the path was changed in `.env`, inspect that configured file instead.

## 3. Main Table

The most important table for memory inspection is:

```text
user_memories
```

This is the current source of truth for persistent user memory when using the SQLite backend.

## 4. Fields To Inspect First

The most useful columns to inspect are:

- `platform`
- `external_user_id`
- `last_known_username`
- `user_profile`
- `conversation_summary`
- `stable_facts_json`
- `preferences_json`
- `relationship_notes_json`
- `working_memory_buffer_json`
- `last_seen_at`
- `updated_at`

## 5. What Each Column Means

### Identity

- `platform`
- `external_user_id`
- `last_known_username`

These identify who the memory belongs to.

### Persistent structured memory

- `stable_facts_json`
- `preferences_json`
- `relationship_notes_json`

These are long-term memory layers.

### Continuity and episodic layers

- `conversation_summary`
- `working_memory_buffer_json`

Short version:

```text
conversation_summary = compact continuity
working_memory_buffer_json = medium-term episodic fragments
```

### Timestamps

- `last_seen_at`
- `updated_at`

These help verify whether the memory is being updated when expected.

## 6. DB Browser Workflow

Suggested workflow in DB Browser for SQLite:

1. Open DB Browser for SQLite.
2. Open the database file:
   - `data/social_chatbot.sqlite3`
3. Go to:
   - `Browse Data`
4. Select table:
   - `user_memories`
5. Inspect rows directly.

Best first checks:

- verify that one row exists per `platform + external_user_id`
- inspect whether `stable_facts_json` contains expected facts
- inspect whether `preferences_json` contains expected preferences
- inspect whether `conversation_summary` is compact
- inspect whether `working_memory_buffer_json` stays short and coherent
- inspect whether `updated_at` changes after a new message

## 7. DBeaver Workflow

Suggested workflow in DBeaver:

1. Create a new SQLite connection.
2. Point it to:
   - `data/social_chatbot.sqlite3`
3. Open the `user_memories` table.
4. Use table view for browsing and filtering.

DBeaver is especially useful if you want:

- filters
- sorting by timestamp
- repeated inspection sessions

## 8. Useful SQLite Queries

If you want a faster inspection path in DB Browser or `sqlite3`, these queries are useful.

### Show all memories

```sql
SELECT
  platform,
  external_user_id,
  last_known_username,
  updated_at
FROM user_memories
ORDER BY updated_at DESC;
```

### Inspect one user memory

```sql
SELECT
  platform,
  external_user_id,
  last_known_username,
  user_profile,
  conversation_summary,
  stable_facts_json,
  preferences_json,
  relationship_notes_json,
  working_memory_buffer_json,
  last_seen_at,
  updated_at
FROM user_memories
WHERE platform = 'instagram'
  AND external_user_id = 'user-1';
```

### Find memories with working memory content

```sql
SELECT
  platform,
  external_user_id,
  working_memory_buffer_json,
  updated_at
FROM user_memories
WHERE working_memory_buffer_json != '[]'
ORDER BY updated_at DESC;
```

### Find memories with stable facts

```sql
SELECT
  platform,
  external_user_id,
  stable_facts_json,
  updated_at
FROM user_memories
WHERE stable_facts_json != '[]'
ORDER BY updated_at DESC;
```

### Find memories with preferences

```sql
SELECT
  platform,
  external_user_id,
  preferences_json,
  updated_at
FROM user_memories
WHERE preferences_json != '[]'
ORDER BY updated_at DESC;
```

## 9. How To Read The JSON Columns

The `_json` columns store serialized lists.

Examples:

```text
stable_facts_json = ["me llamo Marcos"]
preferences_json = ["prefiero respuestas cortas"]
working_memory_buffer_json = ["The user is working on a project and wants the next concrete step."]
```

These are not separate tables yet.

That is acceptable for the current phase, but it means visual inspection should expect JSON arrays inside cells.

## 10. Recommended Debugging Routine

When debugging memory, use this order:

1. inspect the stored row in SQLite
2. inspect app-shaped memory with:
   - `scripts/inspect_user_memory.py`
3. inspect prompt-level selected memory with:
   - `scripts/inspect_llm_prompt.py`

Compare:

- what is stored
- what is selected
- what is sent to the model

This gives the clearest mental model of memory behavior.

## 11. Practical Conclusion

For Phase 25, the official visual inspection path should be:

```text
DB Browser for SQLite for direct visual storage inspection
+ inspect_user_memory.py for app-shaped inspection
+ inspect_llm_prompt.py for prompt-level inspection
```

This is enough to consider SQLite memory inspection practical and usable without building a custom UI yet.
