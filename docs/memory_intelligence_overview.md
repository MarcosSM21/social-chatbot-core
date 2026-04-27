# Memory Intelligence Overview

## Where We Are

The project already has:

- persistent memory:
  - `stable_facts`
  - `preferences`
  - `relationship_notes`
  - `conversation_summary`
  - `last_known_username`
  - `last_seen_at`
- recent history
- `retrieved_memory`
- `retrieval_strategy`
- a first lightweight `working_memory_buffer`

## What We Already Learned

- the problem is not only remembering more
- the problem is injecting better context into the prompt
- `conversation_summary` should stay compact
- a future `LLMMemoryOrchestrator` makes sense
- a `working_memory_buffer` is a better place for broader medium-term context than an oversized summary

## Current Direction

Target long-term flow:

```text
recent_history
+ persistent_memory
+ working_memory_buffer
-> LLMMemoryOrchestrator
-> compact structured memory
-> conversational model
```

## What Is Still Missing

- better rules for what should enter persistent memory
- better compactation of prompt context
- a mature use of `working_memory_buffer`
- a future orchestrator layer
- simple SQLite inspection tooling

## Current Status

Phase 22 is not fully closed yet.

It is already well oriented, but still in the middle of turning:

```text
memory architecture
```

into:

```text
memory intelligence
```

## Practical Next Step

When continuing Phase 22, the best next focus is:

```text
decide how the lightweight working_memory_buffer should interact with selection and compaction,
without introducing heavy latency or too much complexity at once
```
