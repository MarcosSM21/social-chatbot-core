# Context Compaction Goal

This document defines the goal of context compaction during Phase 26.

The project already has meaningful memory layers and retrieval logic.

The next problem is no longer:

```text
how do we store more context
```

The next problem is:

```text
how do we send less but better context to the model on a given turn
```

## 1. What Context Compaction Means

Context compaction means turning:

- recent history
- persistent memory
- working memory
- turn-level retrieved memory

into a final context block that is:

- smaller
- less redundant
- easier for the model to use
- better aligned with the current user message

The goal is not to remove useful context.

The goal is to stop sending overlapping or low-value context just because it exists somewhere in memory.

## 2. Why This Phase Matters

The project now has enough memory structure that prompt quality depends not only on what is stored, but also on how that memory is packaged for the model.

Without compaction, the system risks:

- repeated information across multiple memory layers
- prompt bloat
- weaker prioritization
- a less clear signal about what matters on this turn

## 3. Current Inputs That Compete For Prompt Space

The current system may draw from:

- `recent_history`
- `stable_facts`
- `preferences`
- `relationship_notes`
- `conversation_summary`
- `working_memory_buffer`
- `retrieved_memory`

These layers are useful, but they do not all deserve equal prompt authority on every turn.

## 4. Main Goal Of Phase 26

The main goal of this phase is:

```text
make the final turn-level context more explicit, more selective, and less repetitive
```

That means moving closer to a model where:

- total memory exists
- some memory is selected
- a smaller final compacted context is sent to the model

## 5. What Good Compaction Should Achieve

Good context compaction should:

- prefer relevant memory over merely available memory
- reduce duplication between layers
- preserve structured high-value memory when needed
- preserve situational context when needed
- avoid turning the prompt into a dump of all memory layers

## 6. What This Phase Is Not

Phase 26 is not yet:

- embeddings
- vector retrieval
- full semantic clustering
- an `LLMMemoryOrchestrator`

This phase is still a lighter and more controllable step.

Its job is to improve context quality before moving to more advanced orchestration.

## 7. The Direction

The desired direction is:

```text
memory layers
-> retrieval
-> compacted turn context
-> prompt
```

Instead of:

```text
memory layers
-> prompt directly
```

## 8. One-Line Rule

```text
Phase 26 should make the final prompt context smaller, cleaner, and more intentional than the raw sum of all available memory layers
```
