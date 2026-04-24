# Memory Architecture

This document defines how memory should work in the project before implementing deeper memory intelligence.

The goal is to make memory explicit, stable, inspectable, and future-proof.

Memory is not the same thing as logs, raw payloads, or full chat history.

## 1. Purpose Of Memory

Memory exists to help the chatbot respond with better continuity, personalization, and relevance.

A good memory system should help the assistant:

- remember stable facts about a user
- remember useful preferences
- keep lightweight continuity across conversations
- avoid repeating the same discovery every time
- feel more coherent over time

A good memory system should not:

- store everything blindly
- store sensitive data
- become a dump of every message ever sent
- replace full chat history
- replace operational traces
- invent facts that were never grounded

## 2. Identity Of A User

The canonical identity for memory should be:

```text
platform + external_user_id
```

Example:

```text
platform=instagram
external_user_id=<instagram_scoped_user_id>
```

This should remain the primary key for memory.

Why:

- it is stable enough for the current integration
- it is what the Instagram messaging flow actually gives us
- it survives FastAPI restarts and Cloudflare tunnel restarts
- it is the correct technical identity for the current system

## 3. Human-Friendly Identification

Besides the canonical identity, memory should eventually store human-friendly identifiers.

Examples:

```text
last_known_username
last_seen_at
```

These fields should help debugging and manual inspection.

Important rule:

```text
human-friendly identifiers are not primary identity
```

Usernames can change, so they must not replace:

```text
platform + external_user_id
```

## 4. What Memory Is Not

Memory must not be confused with the following:

### Raw provider payloads

These are raw incoming webhook payloads.

Path today:

```text
data/provider_raw_payloads.json
```

Role:

```text
debugging
provider inspection
webhook troubleshooting
```

These are not memory.

### External traces

These are operational records of what happened.

Path today:

```text
data/external_traces.json
```

Role:

```text
inbound/outbound audit
operational status
error tracking
delivery debugging
```

These are not memory.

### Chat history

This is the recent conversation history used for local continuity.

Path today:

```text
data/chat_history.json
```

Role:

```text
short-term turn history
recent context
session continuity
```

This is not long-term memory.

## 5. Memory Layers

The system should think about memory in layers.

### Layer 1: Identity memory

Things that identify or anchor the user.

Examples:

```text
name
last_known_username
```

### Layer 2: Stable facts

Things that are likely to remain true for a long time.

Examples:

```text
me llamo Marcos
I study engineering
I live in Madrid
```

These must be high-confidence and low-risk.

### Layer 3: Preferences

Things about how the user likes interacting.

Examples:

```text
prefiero respuestas cortas y sin rodeos
me gusta que me digas una cosa concreta
```

These are highly valuable for conversation quality.

### Layer 4: Relationship notes

Interaction-level notes that describe the conversational dynamic.

Examples:

```text
user likes quick replies
user tends to ask reflective questions
user responds well to teasing tone
```

This layer should be used carefully to avoid overfitting or creepiness.

### Layer 5: Conversation summary

A compact rolling summary of useful recent context.

This is not supposed to become a full transcript.

Its role is:

```text
carry continuity
compress useful recent context
support future retrieval
```

## 6. Current Memory Fields

Current `UserMemory` model:

```text
platform
external_user_id
user_profile
conversation_summary
stable_facts
preferences
relationship_notes
updated_at
```

This is a good base, but it is still only a first version.

## 7. Future Memory Fields

Possible future additions:

```text
last_known_username
last_seen_at
memory_version
memory_confidence
memory_source
```

Possible future advanced structure:

```text
ephemeral memory
long-term memory
retrieved relevant memory
```

These do not need to be implemented immediately, but the architecture should leave room for them.

## 8. What Should Not Be Stored

Memory should never store sensitive data.

Examples:

```text
passwords
tokens
access_token
api key
.env contents
dni
bank data
credit card data
private credentials
```

Memory should also avoid storing useless noise.

Examples:

```text
one-off filler messages
empty messages
messages with no lasting value
repeated trivial remarks
```

## 9. What Should Eventually Be Remembered

Memory should prefer information that is:

- stable
- reusable
- relevant across future turns
- helpful for tone or continuity
- safe to store

Examples:

```text
name
communication style preference
important recurring topic
relationship dynamic preference
important long-running personal/project context
```

## 10. Storage Direction

Current state:

- JSON memory repository exists
- SQLite memory repository exists

Direction:

```text
SQLite should become the serious default for memory
```

Reason:

- easier querying
- easier inspection
- better fit for future scaling
- easier future migration to PostgreSQL

JSON can still exist for simple local modes or tests, but memory architecture should conceptually target structured storage.

## 11. Debugging And Inspection

Memory must be easy to inspect.

This is required for:

- debugging
- trust
- manual review
- future tuning

Recommended local tools:

```text
DB Browser for SQLite
DBeaver
sqlite3 CLI
```

If memory cannot be inspected, it cannot be trusted.

## 12. Non-Text Inputs

The memory architecture must be ready for inputs that are not plain text.

Examples:

```text
image
audio
video
call
empty message
```

Initial rule:

```text
do not accidentally treat unsupported media as meaningful memory
```

Future phases should define explicit policy for each media type.

## 13. Scaling Perspective

If the project grows to many users, memory cannot depend on flat JSON files forever.

SQLite is an acceptable intermediate step.

Future scalable direction:

```text
SQLite
-> PostgreSQL
```

This should preserve the same logical memory contract.

Important principle:

```text
changing storage backend should not change conversational behavior
```

## 14. Retrieval Future

The future of memory is not only storing information, but selecting the right information.

Later phases may add:

```text
memory retrieval
memory ranking
LLM-assisted memory selection
RAG over memory
```

That future should be built on top of a clean memory structure, not on top of noisy logs or raw transcripts.

## 15. Design Principles

The memory system should follow these principles:

- stable identity first
- safe memory first
- inspectable memory first
- selective memory over exhaustive memory
- structured memory over accidental memory
- storage backend should be replaceable
- future retrieval should be possible without redesigning everything

## 16. Current Direction

Phase 21 is not about making memory smarter immediately.

It is about making memory:

- explicit
- serious
- debuggable
- scalable
- ready for future retrieval intelligence
