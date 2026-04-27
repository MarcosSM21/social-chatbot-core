# Memory Persistence Policy

This document defines the current policy for deciding what should enter persistent memory, what should stay in working memory, and what should not be stored at all.

The goal of this phase is not only to remember more, but to remember better.

## 1. Why This Policy Exists

The project already has several memory layers:

- `stable_facts`
- `preferences`
- `relationship_notes`
- `conversation_summary`
- `working_memory_buffer`
- recent history

That is useful, but without a persistence policy the system can still drift into:

- storing too much
- storing the wrong things
- storing temporary context as if it were permanent
- duplicating the same idea across several layers
- letting ambiguous fields like `user_profile` do too many jobs

This policy exists to reduce that drift.

## 2. Main Principle

The system should prefer:

```text
store less, but store higher-quality memory
```

Persistent memory should contain information that is:

- reusable
- stable or likely to matter again
- safe to keep
- helpful across future turns or future sessions

Persistent memory should not become:

- a full transcript
- a dump of every user message
- a short-term scratchpad
- a substitute for recent history

## 3. Memory Categories

### A. Persistent identity memory

Examples:

```text
me llamo Marcos
```

Destination:

- `stable_facts`

Characteristics:

- high-confidence
- likely to remain true
- useful again in future turns

### B. Persistent preference memory

Examples:

```text
prefiero respuestas cortas
me gusta que me digas una cosa concreta
```

Destination:

- `preferences`

Characteristics:

- changes how the assistant should respond
- likely to stay useful across multiple conversations

### C. Relationship memory

Examples:

```text
user dislikes overexplaining
user responds better to direct tone
```

Destination:

- `relationship_notes`

Characteristics:

- should be conservative
- should not rely on weak inference
- should only exist when useful and reasonably grounded

### D. Medium-term working memory

Examples:

```text
the user is tired but wants to keep making progress with the project
the current conversation is focused on memory design and architecture
```

Destination:

- `working_memory_buffer`

Characteristics:

- useful for medium-term continuity
- may matter again soon
- not yet clearly worthy of long-term persistent storage

### E. Compact continuity memory

Examples:

```text
The user is tired but wants to keep making progress with the project.
```

Destination:

- `conversation_summary`

Characteristics:

- compact
- continuity-oriented
- should remain smaller and cleaner than a working-memory buffer

## 4. What Should Go To Persistent Memory

The system should prefer persistent storage for:

- user name
- stable personal facts explicitly stated by the user
- durable interaction preferences
- strong recurring communication preferences
- grounded relationship notes that affect future replies

Typical examples:

```text
me llamo Marcos
prefiero respuestas cortas
me gusta que me des una sola recomendación concreta
```

## 5. What Should Stay Out Of Persistent Memory

The system should avoid persistent storage for:

- one-off emotional states
- temporary plans
- single-turn situational details
- filler messages
- weak guesses about personality
- contextual details that only matter right now

Examples:

```text
hoy estoy cansado
ahora mismo estoy en el metro
estoy escribiendo rápido
```

These may still be useful, but they belong more naturally in:

- recent history
- `working_memory_buffer`
- or a compact short-term summary

## 6. What Should Not Be Stored At All

The system should never persist:

- passwords
- tokens
- API keys
- `.env` contents
- private credentials
- bank data
- credit card data
- DNI-like sensitive identifiers
- secret internal instructions

The system should also avoid storing:

- empty content
- non-usable provider noise
- unsupported media as if it were text memory

## 7. Persistent Memory vs Working Memory

This is one of the most important distinctions.

### Persistent memory

Use when:

- the information is likely to matter again across sessions
- the information is reasonably stable
- the information changes how future replies should work

### Working memory

Use when:

- the information is useful now or soon
- the information may influence upcoming turns
- the information is too contextual or too temporary to deserve long-term storage yet

This means many things should first enter:

```text
working_memory_buffer
```

and only later, if they prove durable and useful, be promoted into more persistent layers.

## 8. Role Of conversation_summary

`conversation_summary` should not be treated as long-term free-form storage.

Its role should remain:

- continuity fallback
- compact situational compression
- prompt-friendly summary layer

It should not become:

- a transcript substitute
- the main working-memory store
- the only source for future orchestration

That is why `working_memory_buffer` exists separately.

## 9. Role Of user_profile

`user_profile` is currently useful, but semantically overloaded.

Today it still acts partly like:

- a convenience field
- a merged memory field
- a legacy catch-all

Directionally, the project should reduce its ambiguity over time.

Long-term preference:

```text
structured fields should become more important than user_profile
```

This does not require removing `user_profile` immediately, but it does mean:

- avoid giving it too much authority
- avoid duplicating everything into it
- prefer clearer structured destinations where possible

## 10. Promotion Logic Direction

The project is not fully implementing promotion logic yet, but the intended direction is:

### Promote to persistent memory when:

- the information is explicitly stated
- the information is likely stable
- the information affects future reply quality
- the information appears durable or repeated

### Keep only in working memory when:

- the information is situational
- the information may matter soon, but not necessarily later
- the information is too vague or too early to promote

### Drop or ignore when:

- the information is noise
- the information is unsafe
- the information has no clear future value

## 11. Current Policy Preference

If the system is unsure, it should prefer this order:

```text
recent_history
-> working_memory_buffer
-> compact summary
-> persistent memory
```

That is safer than aggressively persisting everything.

In other words:

```text
uncertain memory should usually stay temporary first
```

## 12. Why This Policy Matters For Future Phases

This policy prepares the project for:

- better working-memory management
- better compactation
- future promotion rules
- future pruning rules
- a future `LLMMemoryOrchestrator`

Without this policy, memory intelligence would grow on top of ambiguous storage decisions.

## 13. Main Takeaway

The project should not treat all memory as equally deserving of persistence.

The guiding rule is:

```text
stable and reusable information deserves persistent memory
temporary and situational information deserves working memory
unsafe or useless information deserves no memory
```
