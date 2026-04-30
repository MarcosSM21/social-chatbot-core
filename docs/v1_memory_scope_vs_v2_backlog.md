# V1 Memory Scope Vs V2 Backlog

This document separates the memory scope that belongs to V1 from the memory improvements that should explicitly wait for V2.

Its purpose is to prevent endless iteration and make release decisions easier.

## 1. Decision Rule

The rule is:

```text
V1 memory must be good enough to support a real product release.
V2 memory can become smarter after production feedback exists.
```

This means:

- V1 is not the final form of memory
- V1 should still be demanding and serious
- V2 is where deeper memory intelligence should reopen

## 2. What Belongs To V1

V1 memory should already provide:

- stable user identity memory
- basic user preference memory
- recent conversation continuity
- medium-term working memory
- turn-level relevant memory retrieval
- basic prompt compaction
- SQLite persistence
- inspection and debugging paths

### Concretely, V1 memory includes

- `stable_facts`
- `preferences`
- `relationship_notes` in a conservative form
- `conversation_summary`
- `working_memory_buffer`
- `retrieved_memory`
- `retrieved_memory_reasons`
- rule-based `Compacted turn context`
- SQLite as the serious backend
- prompt inspection
- user-memory inspection
- visual SQLite inspection workflow

### V1 quality bar

V1 memory should satisfy all of these:

- identity and preferences are remembered reliably
- situational context can survive beyond the immediate last turn
- memory does not become obvious prompt spam
- memory does not persist obvious sensitive content
- memory is inspectable enough to debug with confidence
- memory behaves consistently enough for real users

## 3. What Does Not Need To Enter V1

These ideas are valuable, but they are not required to ship V1:

- embeddings
- vector retrieval
- vector databases
- semantic clustering
- multimodal memory
- a full `LLMMemoryOrchestrator`
- agent memory
- advanced long-gap conversation continuity
- sophisticated emotional-state modeling

These should be treated as:

```text
valuable future upgrades, not V1 blockers
```

## 4. What Belongs To V2

V2 should reopen memory around smarter understanding, not around basic storage.

### Strong V2 candidates

- episode boundaries
- stronger relationship context
- stronger current-state context
- smarter compaction
- semantically richer retrieval
- embeddings
- vector memory search
- experimental `LLMMemoryOrchestrator`

## 5. Why This Split Makes Sense

V1 is already close to being strong enough because it solves:

- storage
- persistence
- retrieval
- compaction
- observability

That means the next wave of memory work should not block shipping.

The next wave should be driven by:

- real usage
- real failure cases
- real evidence of where rule-based memory stops being enough

## 6. Learning Perspective

Working on V1 memory is still strongly aligned with future learning goals.

Why:

- it teaches memory architecture
- it teaches retrieval and compaction
- it teaches prompt authority
- it teaches observability
- it creates the right foundation for RAG and vector retrieval later

This means:

```text
V1 is not a distraction from RAG, embeddings, or advanced memory.
V1 is the foundation that makes those topics easier to understand and use well in V2.
```

## 7. Practical Release Rule

When a memory improvement appears, ask:

```text
does this materially improve the chatbot before the V1 deadline?
```

If the answer is no, it should go to V2.

## 8. One-Line Rule

```text
V1 memory should be reliable, useful, compact, safe, and inspectable; V2 memory should become semantically smarter
```
