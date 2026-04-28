# Compacted Turn Context Contract

This document defines the initial target shape of the final compacted context for a conversational turn.

Its purpose is to separate:

- total available memory
- selected memory
- final prompt-ready context

The project already stores and retrieves memory.

The next step is to define a cleaner structure for:

```text
what should actually reach the model on this turn
```

## 1. Why This Contract Exists

Without an explicit final context contract, the system risks treating all useful layers as prompt-facing at the same time.

That leads to:

- redundancy
- prompt bloat
- unclear authority between layers
- harder future migration toward a more advanced orchestrator

This contract is meant to work for both:

- a rule-based compaction pipeline
- a future `LLMMemoryOrchestrator`

## 2. Initial Target Shape

The compacted turn context should move toward a structure like this:

```json
{
  "identity_context": [],
  "preference_context": [],
  "current_topic_context": [],
  "current_state_context": [],
  "relationship_context": null,
  "episode_continuity": null,
  "compaction_strategy": "rule_based_compaction_v1"
}
```

This does not need to be implemented exactly as JSON.

It is a conceptual contract for the final context package.

## 3. Field Meaning

### `identity_context`

Purpose:

- who this person is
- durable identity-level context

Likely sources:

- `stable_facts`
- limited fallback from `user_profile`

Examples:

```text
me llamo Marcos
I work in product design
```

This should stay concise.

### `preference_context`

Purpose:

- what this user tends to like or dislike in conversation
- what response shape tends to work better

Likely sources:

- `preferences`

Examples:

```text
prefiere respuestas cortas
no le gusta que le sobreexpliquen
```

This should only include preferences relevant to how the assistant should answer.

### `current_topic_context`

Purpose:

- what the conversation is mainly about right now
- what active topic the model should stay anchored to

Likely sources:

- `retrieved_memory`
- `working_memory_buffer`
- `recent_history`

Examples:

```text
the user is refining the memory architecture
the user wants the next practical step for the project
```

This is likely one of the most important fields.

### `current_state_context`

Purpose:

- how the user seems to be right now
- current emotional or situational state when it is useful and grounded

Likely sources:

- `working_memory_buffer`
- `conversation_summary`
- sometimes recent turns

Examples:

```text
the user is tired but wants to keep making progress
the user feels a bit overwhelmed but wants clarity
```

This should remain conservative and grounded in explicit signals.

### `relationship_context`

Purpose:

- what shared history exists between the assistant and this user
- what kind of ongoing conversational relationship this seems to be
- what broad themes have historically defined the interaction

Important clarification:

```text
relationship_context does not only mean tone habits
```

Here it should mainly represent:

- shared history
- recurring topics
- type of bond or interaction context

Examples:

```text
we often talk about the user's project and system design decisions
this interaction has mostly revolved around practical problem-solving
this feels more like a work/project relationship than a casual chat
```

This field can be weak or empty for now, but its meaning should stay clear.

### `episode_continuity`

Purpose:

- whether this turn clearly continues a recent conversational episode
- or whether it feels more like a fresh conversational restart

Examples:

```text
continuing the same active conversation about memory architecture
starting a new conversation after a long gap
```

This field does not need to be sophisticated yet.

For now, it can remain light or even mostly unused.

## 4. Expected Source Hierarchy

This contract suggests a hierarchy like:

```text
memory layers
-> retrieval / selection
-> compacted turn context
-> prompt
```

Instead of:

```text
memory layers
-> prompt directly
```

## 5. Why This Shape Is Useful

This shape gives the system:

- a cleaner boundary between stored memory and prompt memory
- a better future slot for smarter orchestration
- a more human-readable way to think about conversational context
- a safer path to reducing redundancy

## 6. What This Contract Does Not Assume

This contract does not assume:

- embeddings
- vector retrieval
- semantic clustering
- an LLM orchestrator on every turn

It is intentionally compatible with a simpler rule-based implementation first.

## 7. Initial Implementation Philosophy

The first implementation does not need to fill every field equally well.

A realistic first version might be:

- `identity_context`
  - light but useful
- `preference_context`
  - useful when relevant
- `current_topic_context`
  - strongest field
- `current_state_context`
  - conservative
- `relationship_context`
  - mostly weak or empty at first
- `episode_continuity`
  - minimal or placeholder

That is acceptable.

The key is to create the structure first, then improve how it is populated.

## 8. One-Line Rule

```text
The compacted turn context should represent the small set of identity, preference, topic, state, relationship, and continuity signals that matter most for answering this turn well
```
