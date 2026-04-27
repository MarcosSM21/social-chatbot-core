# Memory Layers Reference

This document is a quick reference for the different memory and context layers in the project.

Its purpose is to make it easier to answer recurring questions such as:

- what is recent history vs persistent memory
- what is `conversation_summary` vs `working_memory_buffer`
- what is actually sent to the prompt on a given turn

## Quick Comparison

| Layer | What it is | Horizon | What it stores | Goes directly into the prompt | Example |
|---|---|---:|---|---|---|
| `recent_history` | last real turns of the conversation | short-term | recent user/assistant messages | yes | "The user asked this 2 turns ago" |
| `stable_facts` | durable user facts | long-term | name, stable identity facts | yes, when relevant | `me llamo Marcos` |
| `preferences` | durable interaction preferences | long-term | response style or conversational preferences | yes, when relevant | `prefiero respuestas cortas` |
| `relationship_notes` | conservative notes about interaction patterns | long-term | useful relationship-level patterns | yes, when relevant | `no le gusta que le sobreexpliquen` |
| `conversation_summary` | compact continuity summary | medium-term / fallback | useful recent context already summarized | yes, as fallback | `The user is tired but wants to keep making progress...` |
| `working_memory_buffer` | medium-term contextual fragments not yet fully compacted | medium-term | useful recent pieces that may later feed better compaction | no, not directly; first goes through selection | `The user is working on a project and wants the next concrete step.` |
| `retrieved_memory` | memory selected for the current turn | current turn | the most relevant memory for answering now | yes | `Stable fact: me llamo Marcos` |
| `retrieved_memory_reasons` | explanation of why memory was selected | current turn | debugging / traceability | no | `selected stable_fact because it matched the current message` |

## The Most Important Distinction

### `conversation_summary`

This should be understood as:

```text
compact context that is already ready to be used
```

Its role is:

- continuity
- fallback
- a short usable summary
- something that can be injected into the prompt when needed

Mental model:

```text
If I had to explain very quickly to the model what is going on, what would I say?
```

### `working_memory_buffer`

This should be understood as:

```text
intermediate context that is still somewhat raw
```

Its role is:

- keep useful recent fragments
- avoid losing medium-term context too early
- give the selector something more granular than one single summary
- prepare the future path toward stronger memory compaction

Mental model:

```text
What useful recent pieces do I want to keep for now, even if I do not yet know the best final summary?
```

## Practical Difference Today

### `conversation_summary`

Today it acts as:

- an accumulated summary
- more narrative
- a compact fallback layer

### `working_memory_buffer`

Today it acts as:

- a list of medium-term fragments
- more granular than the summary
- not injected directly into the prompt
- a source for future selection

## Short Version

If you only want the fast mental map:

- `recent_history` = what just happened
- `stable_facts` / `preferences` / `relationship_notes` = what we know long-term
- `conversation_summary` = compact context ready to use
- `working_memory_buffer` = intermediate context still useful for future compaction
- `retrieved_memory` = what we actually decided to use for this turn
- `retrieved_memory_reasons` = why that memory was chosen

## One-Line Rule

```text
conversation_summary = compact context ready to use
working_memory_buffer = intermediate context that may later be compacted better
```
