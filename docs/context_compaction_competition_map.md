# Context Compaction Competition Map

This document maps which context layers currently compete for prompt space before Phase 26 introduces stronger compaction behavior.

Its purpose is to make explicit:

- which layers exist
- what each layer is trying to contribute
- where duplication or competition is most likely

## 1. Why A Competition Map Is Needed

The project now has multiple context sources.

That is good for memory quality, but it creates a new problem:

```text
several layers may try to tell the model similar things in different forms
```

Before changing compaction behavior, it is useful to name these competing layers clearly.

## 2. Current Layers That Compete For Prompt Space

### `recent_history`

Role:

- raw short-term continuity
- immediate conversation flow
- recent user intent

Risk:

- may already contain information that also appears in summary or working memory

### `stable_facts`

Role:

- durable identity-level memory
- stable reusable user facts

Risk:

- a fact may also appear inside `user_profile`
- a fact may also be indirectly restated in `retrieved_memory`

### `preferences`

Role:

- durable interaction preferences
- response-style expectations

Risk:

- preference may also appear in `user_profile`
- preference may also be duplicated inside `retrieved_memory`

### `relationship_notes`

Role:

- long-term interaction patterns
- relationship-level hints

Risk:

- may overlap with preferences
- may overlap with selected retrieval notes

### `conversation_summary`

Role:

- compact continuity fallback
- summarized recent useful context

Risk:

- may overlap with `recent_history`
- may overlap with `working_memory_buffer`
- may overlap with `retrieved_memory`

### `working_memory_buffer`

Role:

- medium-term episodic fragments
- situational context not yet fully compacted

Risk:

- may overlap with `conversation_summary`
- may overlap with `recent_history`
- may overlap with `retrieved_memory`

### `retrieved_memory`

Role:

- turn-level selected memory
- the strongest candidate for prompt inclusion

Risk:

- may restate information that already exists in structured memory or summary
- may duplicate concepts that still remain in prompt through other layers

## 3. Where Competition Is Strongest

The strongest competition currently happens in these zones:

### Zone A: `stable_facts` vs `user_profile` vs `retrieved_memory`

These layers may all point to the same identity-level information.

### Zone B: `preferences` vs `relationship_notes` vs `retrieved_memory`

These layers may all try to influence tone or style.

### Zone C: `recent_history` vs `conversation_summary` vs `working_memory_buffer`

These layers may all express recent or medium-term situational context.

### Zone D: `conversation_summary` vs `working_memory_buffer` vs `retrieved_memory`

These layers may all compete to represent what matters most right now.

## 4. Current Hierarchy Is Better Than Before, But Still Incomplete

The project already improved hierarchy by introducing:

- `retrieved_memory`
- `retrieved_memory_reasons`
- `working_memory_buffer`
- better persistence policy

That means context is no longer just dumped into the prompt blindly.

However, the final prompt still risks carrying:

- the selected memory
- the broader summary
- the broader history

without a fully explicit final compacted layer deciding who wins.

## 5. Practical Interpretation

The problem is not that the layers are wrong.

The problem is that several of them may be:

- correct
- useful
- but too similar to all deserve prompt space together

## 6. Desired Outcome Of Phase 26

After this phase, these layers should no longer behave like equal competitors.

Instead, the system should move closer to:

```text
available context
-> selected context
-> compacted final turn context
-> prompt
```

That means some layers should act more like:

- source layers
- candidate layers
- fallback layers

instead of all being prompt-facing with similar weight.

## 7. Most Important Insight

The key insight is:

```text
the system already has enough context;
the next gain comes from choosing better prompt authority, not from adding more layers
```

## 8. One-Line Rule

```text
Phase 26 should turn competing memory layers into a clearer hierarchy where only the most useful final context wins prompt space
```
