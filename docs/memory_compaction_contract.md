# Memory Compaction Contract

This document defines the target shape of compacted conversational memory for the project.

It does not describe the final implementation yet.

Its purpose is to answer a simpler question first:

```text
If a future memory orchestrator had to hand the best compact context to the conversational model,
what should that compact context look like?
```

The current answer is intentionally provisional.

The contract can evolve later, but Phase 22 needs a target structure before improving selectors or introducing an LLM-assisted memory orchestrator.

## 1. Why A Contract Is Needed

Right now, the project already has:

- `user_profile`
- `conversation_summary`
- `stable_facts`
- `preferences`
- `relationship_notes`
- `retrieved_memory`
- `recent_history`

That gives us enough information to answer well, but not yet a single clean compact layer.

Without a target contract, memory work can become scattered:

- one heuristic here
- one extra prompt block there
- one summary fallback somewhere else

The contract exists to prevent that.

It defines what the final compacted memory should contain, even if the way we produce it changes later.

## 2. Current Direction

The long-term direction is:

```text
full memory + relevant history
-> memory compaction/orchestration layer
-> compact structured memory package
-> conversational model
```

At first, this compaction layer may be:

- rule-based
- heuristic
- partially structured

Later, it may become:

- LLM-assisted
- retrieval-aware
- ranking-aware
- multimodal-aware

The contract should survive that evolution.

## 3. Design Goals

A compacted memory package should be:

- short enough to avoid prompt bloat
- structured enough to be inspectable
- expressive enough to preserve useful nuance
- selective enough to remove duplication
- stable enough to support future orchestrators

It should not be:

- a transcript
- an uncontrolled free-text blob
- a duplicate of every memory field we already store
- so rigid that future memory strategies cannot evolve

## 4. Proposed Output Shape

The current target shape is:

```json
{
  "identity": [],
  "preferences": [],
  "relationship": [],
  "situational_context": [],
  "continuity_summary": null,
  "exclusions": [],
  "selection_rationale": []
}
```

This is not yet the persistent storage model.

It is the target output of the future memory compaction layer for one turn.

## 5. Field Meanings

### identity

High-confidence user anchors that matter for continuity.

Examples:

```text
me llamo Marcos
```

Typical source:

- `stable_facts`
- selected identity items from `user_profile`

Rules:

- keep very short
- only include identity facts that are useful for this turn
- avoid repeating the same fact elsewhere

### preferences

User preferences that change how the assistant should answer.

Examples:

```text
prefiero respuestas cortas
me gusta que me digas una cosa concreta
```

Typical source:

- `preferences`
- selected preference-like items from `user_profile`

Rules:

- prioritize things that affect tone, format, or helpfulness
- avoid stale or low-value preferences

### relationship

Useful notes about the interaction dynamic.

Examples:

```text
user responds better to direct tone
user dislikes overexplaining
```

Typical source:

- `relationship_notes`
- future higher-confidence interaction summaries

Rules:

- avoid over-psychologizing the user
- avoid vague or creepy inferences
- keep this layer conservative

### situational_context

Short-lived or medium-lived context that matters for the current turn.

Examples:

```text
the user is tired but wants to keep making progress with the project
the user is asking for the next concrete step
```

Typical source:

- `conversation_summary`
- selected recent history
- future situational extraction

Rules:

- this is where we keep “what is going on right now”
- should not become a second transcript
- should not repeat identity or preference data if already captured elsewhere

### continuity_summary

Optional compact free-text continuity fallback.

Example:

```text
The conversation is about the user's project, and the user currently wants practical next steps without a long explanation.
```

Typical source:

- `conversation_summary`
- future orchestrator output

Rules:

- use only when structured fields are not enough
- should be one compact sentence or short paragraph
- should never become a dump of repeated memory

### exclusions

Optional list of things the compaction layer intentionally decided not to include.

Examples:

```text
omitted duplicated preference already covered in preferences
omitted recent history because summary already captures it
```

This field is mainly for debugging and inspection.

It may not be included in the final prompt sent to the conversational model.

### selection_rationale

Optional trace of why certain items were selected.

Examples:

```text
selected identity because the user asked whether the assistant remembered the name
selected situational context because the current message is still about the project
```

This field is also mainly for debugging and inspection.

It is part of the compaction contract so that future rule-based or LLM-based selectors remain interpretable.

## 6. What This Contract Is Not

This contract is not:

- the SQLite schema
- the persistent `UserMemory` dataclass
- the raw output of recent history
- the raw output of `retrieved_memory`
- the exact final prompt format

It is the bridge between:

```text
memory storage
```

and:

```text
prompt-ready compact context
```

## 7. Relationship To Current Structures

Current structures remain valid.

This contract does not replace them yet.

Instead, it gives them a convergence target.

Approximate mapping today:

```text
stable_facts           -> identity
preferences            -> preferences
relationship_notes     -> relationship
conversation_summary   -> situational_context / continuity_summary
recent_history         -> situational_context
retrieved_memory       -> early retrieval signal
user_profile           -> mixed legacy source, should be interpreted carefully
```

## 8. Why This Shape Makes Sense

This structure tries to balance two competing goals:

### Goal A: compactness

We do not want the final prompt to become a pile of memory blocks that say the same thing in different words.

### Goal B: usefulness

We do not want compactation to flatten everything into one vague summary blob.

This contract allows both:

- structured slots for important categories
- one fallback summary field
- inspection fields for debugging

## 9. Minimum Viable Version

The first practical version does not need every field populated.

A perfectly acceptable early compacted output could be:

```json
{
  "identity": ["me llamo Marcos"],
  "preferences": ["prefiero respuestas cortas"],
  "relationship": [],
  "situational_context": ["the user is tired but wants to keep making progress with the project"],
  "continuity_summary": null,
  "exclusions": [],
  "selection_rationale": [
    "selected identity because the user asked about remembered information",
    "selected preference because it affects response style"
  ]
}
```

That is already enough to be meaningfully better than blindly injecting every memory layer.

## 10. Future Evolution

This contract is intentionally compatible with future improvements such as:

- better rule-based compaction
- scoring/ranking of memory candidates
- LLM-assisted deduplication
- LLM-assisted summarization
- RAG over memory
- multimodal context compaction

The compaction mechanism may change.

The output shape should remain recognizable.

## 11. Immediate Use In Phase 22

This contract gives the next steps a concrete direction:

1. improve rule-based selectors toward this shape
2. reduce duplication between current prompt memory blocks
3. make selection reasoning more visible
4. later replace or augment rule-based logic with an LLM intermediary

## 12. Main Takeaway

The important shift is this:

```text
We do not want memory fields to compete directly inside the prompt.
We want them to be transformed first into one compact, structured memory package.
```

That compact package is the real target of Memory Intelligence.
