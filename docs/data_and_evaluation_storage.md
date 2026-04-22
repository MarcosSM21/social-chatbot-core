# Data And Evaluation Storage

This document explains where runtime data, evaluation data, generated reports, and versioned test cases live.

## Runtime Data

Runtime data is local operational data created while the chatbot is running.

Path:

```text
data/
```

Examples:

```text
data/chat_history.json
data/conversation_mappings.json
data/external_traces.json
data/provider_raw_payloads.json
data/user_memories.json
data/social_chatbot.sqlite3
```

This folder is ignored by Git because it may contain:

- real Instagram payloads
- user messages
- user memory
- traces
- local SQLite databases
- operational state

Do not commit `data/`.

## Evaluation Cases

Evaluation cases are versioned because they describe the scenarios we want to test.

Path:

```text
evaluation/cases/
```

Examples:

```text
evaluation/cases/instagram_dm_cases.json
evaluation/cases/multiturn_conversation_cases.json
```

These files should be committed.

They are part of the project logic because they define what we expect from the chatbot.

## Evaluation Runtime

Evaluation runtime data is temporary data created while running evaluations.

Path:

```text
evaluation/runtime/
```

Examples:

```text
evaluation/runtime/user_memories.json
evaluation/runtime/chat_history.json
evaluation/runtime/multiturn/user_memories.json
evaluation/runtime/multiturn/chat_history.json
```

This folder is ignored by Git.

Evaluation runtime data should not touch real runtime data in `data/`.

## Evaluation Reports

Evaluation reports are generated outputs.

Path:

```text
evaluation/reports/
```

Examples:

```text
evaluation/reports/evaluation_report_*.json
evaluation/reports/evaluation_report_*.md
evaluation/reports/multiturn_report_*.json
evaluation/reports/multiturn_report_*.md
```

This folder is ignored by Git.

Reports are useful for local inspection, but they should not be committed by default.

If a report is especially important, summarize the finding in documentation instead of committing the generated file.

## Storage Backend

User memory can use JSON or SQLite depending on:

```env
MEMORY_STORAGE_BACKEND=json
```

or:

```env
MEMORY_STORAGE_BACKEND=sqlite
```

JSON runtime memory:

```text
data/user_memories.json
```

SQLite runtime memory:

```text
data/social_chatbot.sqlite3
```

Evaluation memory does not use these files. Evaluation scripts use isolated files under:

```text
evaluation/runtime/
```

## Rule Of Thumb

Commit:

```text
app/
tests/
characters/
evaluation/cases/
evaluation/run_*.py
docs/
README.md
requirements.txt
```

Do not commit:

```text
.env
.venv/
.codex
data/
evaluation/runtime/
evaluation/reports/
__pycache__/
*.sqlite3
*.db
```
