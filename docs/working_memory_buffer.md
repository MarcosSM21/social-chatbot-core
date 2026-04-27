# Working Memory Buffer

This document defines a future intermediate memory layer for the project.

The purpose of this layer is to preserve more conversational context than the current compact memory fields, without forcing that broader context directly into the final prompt.

This layer is designed to support a future `LLMMemoryOrchestrator`.

## 1. Why This Layer Exists

The project already distinguishes between:

- recent history
- persistent memory
- compact conversational memory

That is good, but still incomplete for longer conversations.

The current risk is this:

```text
If we try to make conversation_summary hold too much context,
it stops being a summary and becomes a noisy pseudo-transcript.
```

That would create several problems:

- prompt bloat
- unclear semantics
- duplicated context
- harder debugging
- weaker long-term compaction design

The better solution is to introduce a separate intermediate layer:

```text
working_memory_buffer
```

## 2. Intended Role

The `working_memory_buffer` is not the same as:

- recent history
- stable persistent memory
- final compact prompt memory

Its role is:

```text
hold broader medium-term conversational material
that may later be compacted, promoted, or discarded
```

This makes it a staging area between:

```text
raw conversation flow
```

and:

```text
compact structured memory for prompting
```

## 3. Conceptual Position In The Architecture

Target architecture:

```text
recent_history
+ persistent_memory
+ working_memory_buffer
-> memory orchestration / compaction layer
-> compact structured memory package
-> conversational model
```

This means the future system should not depend only on:

- a tiny rolling summary
- a few structured long-term fields

Instead, it should also have access to a broader intermediate memory source.

## 4. What The Working Memory Buffer Should Contain

The buffer should contain medium-term conversational material that is too important to immediately forget, but not yet clearly worthy of long-term persistent memory.

Examples:

- repeated project themes
- short ongoing personal context
- unresolved subtopics
- emotional state relevant to recent turns
- conversation fragments that may matter later

Examples in plain language:

```text
the user is tired but still wants to keep making progress with the project
the user is worried about memory design and long-term architecture
the user has been thinking about deployment and miniPC plans
```

This is broader than a compact summary, but narrower than a transcript of everything.

## 5. What The Buffer Should Not Be

The working buffer should not become:

### Not a transcript

It should not store every turn in full forever.

### Not raw logs

It should not duplicate external traces or webhook payloads.

### Not persistent identity memory

Stable facts and preferences should still have their own long-term places.

### Not final prompt context

The buffer should not be blindly injected into the LLM prompt.

That is one of the most important design constraints.

## 6. Difference From Other Layers

### recent_history

Role:

```text
very recent short-term continuity
```

Typical size:

```text
last few turns
```

### persistent_memory

Role:

```text
structured long-term memory
```

Examples:

- stable facts
- preferences
- relationship notes

### conversation_summary

Role:

```text
compact continuity fallback
```

Should remain short and useful.

### working_memory_buffer

Role:

```text
medium-term memory staging area for future compaction/orchestration
```

This layer gives the system room to think later, without overloading the prompt now.

## 7. Why This Helps Memory Intelligence

Without this layer, the system faces a bad choice:

### Option A

Keep memory very small and risk losing too much conversational context.

### Option B

Make `conversation_summary` too large and muddy the final prompt.

The working buffer avoids that false choice.

It allows:

- more context retention
- later summarization
- later prioritization
- later LLM-assisted compaction

without turning the current prompt into a mess.

## 8. Future Relationship To LLMMemoryOrchestrator

The future `LLMMemoryOrchestrator` should be able to receive:

- persistent memory
- working memory buffer
- recent history
- current user message

And produce:

- compact structured memory package
- updated continuity summary
- possible promotions into persistent memory
- possible pruning of stale working-buffer material

Conceptual flow:

```text
current turn
-> recent_history
-> persistent_memory
-> working_memory_buffer
-> LLMMemoryOrchestrator
-> compact memory for prompt
-> optional memory updates
```

This is the long-term direction.

## 9. When Compaction Should Happen

The orchestrator does not need to run on every turn.

That is important for latency.

Possible triggers:

- working buffer exceeds a character threshold
- working buffer exceeds a turn threshold
- topic shift is detected
- memory cleanup cycle runs
- explicit offline/asynchronous maintenance step

This means the working buffer is compatible with:

- low-latency main conversation flow
- periodic deeper memory compaction

## 10. Why This Is Better Than Making conversation_summary Huge

If `conversation_summary` becomes too large, we lose several things:

- semantic clarity
- compactness
- clean prompt design
- meaningful distinction between layers

If we instead keep:

- `conversation_summary` compact
- `working_memory_buffer` broader

then each layer keeps a clear job.

That makes the architecture easier to evolve and debug.

## 11. What This Document Does Not Decide Yet

This document does not yet decide:

- whether the buffer is stored as one text field or multiple entries
- whether the buffer lives in SQLite immediately
- exact size limits
- exact pruning strategy
- exact trigger conditions
- exact LLM orchestration prompt

Those are later design/implementation questions.

For now, the key architectural decision is simply:

```text
the system needs an intermediate working-memory layer
separate from both compact summary and long-term structured memory
```

## 12. Immediate Direction For Phase 22

This document changes the focus of the phase slightly.

Instead of only asking:

```text
how do we reduce duplication now?
```

we should also ask:

```text
what memory layers do we need so that future compaction is actually good?
```

That means the next practical work should move toward:

- designing how the current selector relates to the future contract
- deciding whether a first lightweight working buffer should exist
- keeping prompt compaction separate from medium-term memory accumulation

## 13. Main Takeaway

The project should not force one field to do too many jobs.

In particular:

```text
conversation_summary should remain compact
working_memory_buffer should carry broader medium-term material
LLMMemoryOrchestrator should later decide how to compact that material well
```

This is the cleanest path toward strong memory intelligence without turning every turn into a latency-heavy orchestration problem immediately.
