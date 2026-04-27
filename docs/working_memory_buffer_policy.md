# Working Memory Buffer Policy

This document defines the intended behavior of `working_memory_buffer` during Phase 24.

Its purpose is to clarify what this layer should keep, what it should reject, and how it should evolve without becoming a mini transcript.

## 1. Role Of The Buffer

`working_memory_buffer` is the project's current conversational episodic memory layer.

It exists to preserve medium-term contextual fragments that are still useful, but are not yet:

- durable enough for persistent memory
- compact enough to replace `conversation_summary`
- ready to be injected wholesale into the prompt

It should be understood as:

```text
useful recent fragments that may later support better retrieval or compaction
```

## 2. What The Buffer Should Store

The buffer should prefer fragments that are:

- situational
- recent
- useful across more than one immediate turn
- not already captured as durable structured memory

Examples:

```text
The user is tired but wants to keep making progress with the project.
The user is worried about how to organize the memory system.
The user wants the next concrete step for the project.
```

## 3. What The Buffer Should Not Store

The buffer should avoid:

- stable identity facts
- durable response preferences
- exact duplicates
- trivial filler
- sensitive information
- near-transcript accumulation

Examples that should usually not enter the buffer:

```text
me llamo Marcos
prefiero respuestas cortas
ok
jajaja
mi contraseña es 1234
```

## 4. Relation To Other Memory Layers

### Versus persistent memory

Persistent memory stores information that is stable and reusable over long periods.

Examples:

- `stable_facts`
- `preferences`
- `relationship_notes`

The buffer should not compete with those layers.

### Versus `conversation_summary`

`conversation_summary` is the compact continuity layer.

`working_memory_buffer` is the fragment layer.

Short version:

```text
conversation_summary = compact continuity already usable
working_memory_buffer = intermediate fragments not yet fully compacted
```

### Versus `recent_history`

`recent_history` contains the actual last turns.

The buffer should not become a second transcript.

Its job is to keep a few useful distilled fragments after the raw turns themselves stop being enough.

## 5. Current Policy

The current implementation already follows some basic rules:

- store turn-level summary fragments, not the full accumulated summary
- avoid exact duplicates
- replace some overlapping fragments when a better version arrives
- keep the buffer short

This is a good starting point, but it is still only an early version.

## 6. Target Behavior For Phase 24

During this phase, the buffer should become better at these decisions:

### 1. When to accumulate

If a new fragment adds genuinely new situational context, it should be added.

### 2. When to replace

If a new fragment says mostly the same thing as an older one, but in a more informative way, the newer one should replace the older one.

### 3. When to ignore

If a new fragment is redundant, trivial, or already represented well enough, it should be ignored.

### 4. When to prune

If the buffer is full, it should not act like a queue only by order.

It should prefer keeping:

- more informative fragments
- more recent fragments
- less redundant fragments

## 7. Design Goal

The design goal is not:

```text
store more context
```

The design goal is:

```text
store fewer but better medium-term fragments
```

## 8. Why This Matters

If the buffer matures well, it becomes:

- a better source for `retrieved_memory`
- a better source for future compaction
- a better foundation for a future `LLMMemoryOrchestrator`

If it matures badly, it becomes:

- noisy
- repetitive
- hard to inspect
- too similar to history or summary

## 9. Phase 24 Direction

Phase 24 should improve `working_memory_buffer` without making it too complex too early.

The expected direction is:

- clearer pruning
- clearer replacement
- clearer novelty detection
- less repetition
- better usefulness as an episodic memory layer

## 10. One-Line Rule

```text
working_memory_buffer should keep a small set of useful medium-term conversational fragments, not a transcript and not a second persistent memory store
```
