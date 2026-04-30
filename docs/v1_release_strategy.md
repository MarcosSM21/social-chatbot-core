# V1 Release Strategy

This document defines the current release strategy for V1.

The goal is to avoid endless iteration and establish a clear rule:

```text
when the V1 checklist is satisfied, the chatbot ships to production
even if it is not perfect
```

## 1. Release Deadline

Current V1 deadline:

```text
May 29, 2026
```

This date is meant to force product decisions, not perfection.

## 2. V1 Release Principle

V1 does not need to be final or state of the art.

It needs to be:

- good enough
- stable enough
- inspectable enough
- safe enough
- useful enough to learn from real usage

Important principle:

```text
the project should not stay trapped in endless private refinement
```

Production will reveal issues.

That is expected.

The purpose of V1 is to ship something real and improve from reality, not to hide until every possible improvement is finished.

## 3. Controlled Production Philosophy

The intended production mindset is:

- release when the checklist is satisfied
- accept that errors will appear
- keep the blast radius controlled
- improve fast from real usage

This is not a reckless launch philosophy.

It is:

```text
real production, but with controlled exposure
```

Examples:

- allowlisted users
- observable logs
- memory inspection available
- rollback path available

## 4. Core V1 Workstreams

The remaining work for V1 should stay focused on these areas:

### 1. Memory

Goal:

- memory should be solid, useful, and inspectable

### 2. Character quality

Goal:

- the bot should feel coherent and natural enough in normal conversations

### 3. Red teaming

Goal:

- basic adversarial and edge-case testing before release

### 4. MiniPC production path

Goal:

- the chatbot should be deployable and operable on the target machine

## 5. V1 Memory Scope

V1 memory should already support:

- stable identity facts
- basic conversation preferences
- recent conversation continuity
- medium-term episodic working memory
- turn-level retrieval
- prompt compaction
- SQLite persistence
- inspection through scripts and visual SQLite tooling

V1 memory does not need to include:

- embeddings
- vector retrieval
- vector databases
- semantic clustering
- multimodal memory
- full LLM orchestration
- advanced episode detection

## 6. V1 Release Checklist

The chatbot is ready to ship V1 when all of the following are true.

### Memory

- remembers identity and simple preferences reliably
- uses relevant memory on a turn
- avoids obvious prompt redundancy
- does not store obvious sensitive memory
- SQLite memory is stable and inspectable

### Conversation quality

- character remains reasonably consistent
- normal conversations feel usable and coherent
- responses are not frequently robotic or obviously broken

### Safety / red teaming

- does not leak secrets or internal instructions in ordinary red-team attempts
- does not fail badly on common adversarial inputs
- handles unsupported or malformed inputs reasonably

### Production readiness

- runs on the target MiniPC
- can restart cleanly
- logs are inspectable
- webhook flow works end-to-end
- updates and rollback are understandable

## 7. V1 Freeze Rule

From this point on, new work should enter V1 only if it clearly improves:

- product quality
- stability
- safety
- deployability

If a change is interesting but not required for release, it should go to V2.

## 8. V2 Direction

V2 is where the project can reopen deeper memory and intelligence work.

Likely V2+ topics:

- episode boundaries
- stronger relationship context
- richer current-state modeling
- smarter compaction
- LLM memory orchestration
- embeddings
- RAG
- vector databases
- agentic extensions

## 9. Practical Conclusion

The current strategy is:

```text
finish a strong V1
ship by May 29, 2026
learn from production
then expand into a more advanced V2
```

## 10. One-Line Rule

```text
V1 is not the end state; it is the first real production version that must be good enough to ship and good enough to learn from
```
