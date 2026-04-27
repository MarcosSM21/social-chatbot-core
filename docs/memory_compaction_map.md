# Memory Compaction Map

This document maps the current memory and context layers used by the project before improving memory intelligence in Phase 22.

The goal is to identify:

- where information is duplicated
- where information overlaps semantically
- where prompt context may grow with unnecessary repetition
- what should later be compacted, prioritized, or excluded

This is not yet the implementation of a smarter selector.

It is the map that explains where the current system is still noisy.

## 1. Current Context Inputs

The current conversational prompt can draw information from these sources:

```text
current_message
recent_history
user_profile
conversation_summary
stable_facts
preferences
relationship_notes
retrieved_memory
character_instructions
safety_instructions
system_instructions
```

Not all of these are equally problematic.

The main focus of this phase is the overlap between:

```text
recent_history
conversation_summary
stable_facts
preferences
relationship_notes
retrieved_memory
```

## 2. Current Memory Layers

### user_profile

Role today:

```text
high-level user memory string
```

Examples:

```text
me llamo Marcos
prefiero respuestas cortas
```

Risk:

- overlaps with `stable_facts`
- overlaps with `preferences`
- can become a mixed bucket instead of a clear memory layer

### stable_facts

Role today:

```text
longer-lived user facts
```

Examples:

```text
me llamo Marcos
```

Risk:

- can duplicate identity information already present in `user_profile`
- may also be implicitly repeated inside `conversation_summary`

### preferences

Role today:

```text
interaction preferences
```

Examples:

```text
prefiero respuestas cortas
me gusta cuando me dices una cosa concreta
```

Risk:

- can overlap with `user_profile`
- can be rephrased again inside `conversation_summary`
- can later also appear in `retrieved_memory`

### relationship_notes

Role today:

```text
notes about conversational dynamic
```

Examples:

```text
user likes quick replies
user responds well to teasing tone
```

Risk:

- can overlap with preferences
- can overlap with character interpretation of the relationship
- can become vague or overly interpretive if not constrained

### conversation_summary

Role today:

```text
rolling compact summary of recent useful context
```

Examples:

```text
The user is tired but still wants to keep making progress with the project.
```

Risk:

- can duplicate facts that already exist elsewhere
- can duplicate recent history
- can duplicate selected memory in `retrieved_memory`
- may become a generic catch-all if it is always used as fallback

### retrieved_memory

Role today:

```text
rule-based turn-level selected memory
```

Examples:

```text
Stable fact: me llamo Marcos
Preference: prefiero respuestas cortas
Summary: The user is tired but wants to keep making progress with the project.
```

Risk:

- duplicates content already separately present in:
  - `stable_facts`
  - `preferences`
  - `relationship_notes`
  - `conversation_summary`
- currently adds a useful layer, but may also increase prompt size until compaction rules improve

## 3. Current Redundancy Patterns

The most important current overlaps are:

### Pattern A: user_profile vs structured memory

Possible duplication:

```text
user_profile = "me llamo Marcos"
stable_facts = ["me llamo Marcos"]
```

Or:

```text
user_profile = "prefiero respuestas cortas"
preferences = ["prefiero respuestas cortas"]
```

Interpretation:

`user_profile` currently behaves partly as a legacy merged field and partly as useful memory.

This makes it convenient, but also ambiguous.

### Pattern B: structured memory vs conversation_summary

Possible duplication:

```text
stable_facts = ["me llamo Marcos"]
conversation_summary = "The user's name is Marcos."
```

Or:

```text
preferences = ["prefiero respuestas cortas"]
conversation_summary = "The user prefers short, direct replies."
```

Interpretation:

The summary may repeat what should already be represented by more stable structured memory.

### Pattern C: structured memory vs retrieved_memory

Possible duplication in prompt:

```text
Known stable facts about this user:
- me llamo Marcos

Relevant memory for this turn:
- Stable fact: me llamo Marcos
```

Interpretation:

This is useful for building retrieval foundations, but noisy if both stay in the final prompt long term.

### Pattern D: conversation_summary vs retrieved_memory

Possible duplication:

```text
Conversation summary: The user is tired but wants to keep making progress with the project.

Relevant memory for this turn:
- Summary: The user is tired but wants to keep making progress with the project.
```

Interpretation:

This is one of the clearest current compactation targets.

### Pattern E: recent_history vs conversation_summary

Possible duplication:

```text
recent_history already contains the recent exchange
conversation_summary repeats the same recent exchange in compressed form
```

Interpretation:

If both are present and short-term history is still available, the prompt may repeat the same idea twice.

## 4. Prompt-Level Redundancy

Today the provider can include:

- full system instructions
- safety instructions
- character instructions
- user_profile
- stable_facts
- preferences
- relationship_notes
- conversation_summary
- retrieved_memory
- recent_history
- current_message

This means the prompt may contain the same semantic idea in multiple forms.

Example:

```text
User profile: prefiero respuestas cortas
Known user preferences:
- prefiero respuestas cortas
Relevant memory for this turn:
- Preference: prefiero respuestas cortas
```

This is not yet a bug, but it is a compaction problem.

## 5. Current Strengths

Even with overlap, the system already has several strong points:

- memory identity is stable
- memory is separated from traces and raw payloads
- prompt preview is inspectable
- retrieved memory already exists as a distinct concept
- recent history is separated from long-term memory
- summary exists as a compact continuity layer

That means the project is well positioned to improve compaction without redesigning everything.

## 6. Current Weaknesses

The main weaknesses now are:

- `user_profile` is semantically overloaded
- duplication is tolerated too often
- `retrieved_memory` is useful but not yet compact enough
- summary fallback may be too eager
- the final prompt can contain repeated memory in several formats
- the system does not yet explain clearly why one memory item won over another

## 7. Compaction Questions For Phase 22

The next steps in memory intelligence should answer these questions:

### Question 1

When should `user_profile` be used, and when should structured memory be enough on its own?

### Question 2

When should `conversation_summary` appear in the prompt, and when should it stay out because recent history or retrieved memory already covers the same information?

### Question 3

Should `retrieved_memory` replace direct prompt injection of full `stable_facts`, `preferences`, and `relationship_notes` in some cases?

### Question 4

How many memory blocks should be allowed into the prompt for one turn?

### Question 5

How can the selector expose clearer reasoning for:

```text
why this memory entered
why this memory was excluded
```

## 8. Immediate Direction

Phase 22 should not try to solve all memory intelligence at once.

The practical direction should be:

1. reduce obvious duplication
2. improve retrieval priority
3. define compactation rules
4. keep prompt context inspectable
5. prepare the path for future LLM-assisted selection

## 9. Main Takeaway

The project already has enough memory structure to support intelligent retrieval.

The current problem is not lack of memory.

The current problem is that memory can still enter the prompt in overlapping forms.

That means the next improvement is not:

```text
remember more
```

but:

```text
inject less, but inject better
```
