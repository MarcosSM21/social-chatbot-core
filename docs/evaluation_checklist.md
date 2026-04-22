# Evaluation Checklist

This document explains how to run automated tests and conversation evaluations without touching real runtime data.

Use it before changing:

- characters
- prompts
- memory behavior
- safety rules
- generation providers
- Instagram webhook behavior

## 1. Run The Test Suite

Use this before committing changes:

```bash
.venv/bin/python -m pytest -q
```

Expected result:

```text
all tests passed
```

Tests should not call:

- Instagram Graph API
- Ollama, unless explicitly mocked or isolated
- Cloudflare tunnel
- real Meta webhooks

## 2. Run Single-Turn Evaluation

Use this to evaluate isolated Instagram DM-like cases.

Mock provider:

```bash
.venv/bin/python evaluation/run_evaluation.py --provider mock
```

Ollama provider:

```bash
.venv/bin/python evaluation/run_evaluation.py --provider ollama
```

Cases live in:

```text
evaluation/cases/instagram_dm_cases.json
```

Generated runtime data lives in:

```text
evaluation/runtime/
```

Generated reports live in:

```text
evaluation/reports/
```

These generated folders are ignored by Git.

## 3. Run Multi-Turn Evaluation

Use this to evaluate continuity, memory, safety, and character behavior across a longer conversation.

Mock provider:

```bash
.venv/bin/python evaluation/run_multiturn_evaluation.py --provider mock
```

Ollama provider with a specific character:

```bash
.venv/bin/python evaluation/run_multiturn_evaluation.py \
  --provider ollama \
  --character-file characters/laia_ambitious_model.json
```

Cases live in:

```text
evaluation/cases/multiturn_conversation_cases.json
```

Runtime data for multi-turn evaluation lives in:

```text
evaluation/runtime/multiturn/
```

Reports are generated as:

```text
evaluation/reports/multiturn_report_*.json
evaluation/reports/multiturn_report_*.md
```

## 4. What Evaluation Does Not Touch

Evaluation should not use real runtime data:

```text
data/
```

Evaluation should not write to:

```text
data/user_memories.json
data/social_chatbot.sqlite3
data/external_traces.json
data/provider_raw_payloads.json
```

Evaluation writes to:

```text
evaluation/runtime/
evaluation/reports/
```

This keeps real Instagram conversations separate from experiments.

## 5. When To Use Mock

Use mock when you want to check:

- evaluation runner works
- test cases are valid JSON
- memory writes happen
- reports are generated
- basic code flow does not crash

Mock is not good for judging:

- naturalness
- character voice
- memory usage in generated replies
- conversational quality

## 6. When To Use Ollama

Use Ollama when you want to judge:

- real conversational quality
- character behavior
- prompt effectiveness
- memory usage in replies
- safety behavior with real model output
- whether a change improves or worsens the actual bot

Before running Ollama evaluation, make sure Ollama is available:

```bash
ollama serve
ollama list
```

## 7. How To Read Reports

Markdown reports are easiest to inspect manually:

```text
evaluation/reports/*.md
```

Look for:

- passed cases
- failed cases
- user message
- assistant response
- memory metadata
- final memory
- failed checks

JSON reports are better for machine inspection:

```text
evaluation/reports/*.json
```

## 8. Common Interpretation Notes

Passing tests does not mean the character is perfect.

Passing evaluation means:

- required safety checks passed
- expected memory behavior happened
- generated response satisfied basic criteria

It does not guarantee:

- perfect style
- perfect emotional nuance
- perfect human realism
- best possible answer

Character tuning should be judged by reading the Markdown report, not only by pass/fail.

## 9. Safe Evaluation Workflow

Recommended workflow before changing production behavior:

```text
1. Edit code, character, or cases
2. Run pytest
3. Run mock evaluation
4. Run Ollama evaluation
5. Read Markdown report
6. Decide whether the change improved behavior
7. Commit only code, docs, characters, tests, and evaluation cases
8. Do not commit runtime or reports
```

## 10. What To Commit

Commit:

```text
evaluation/cases/
evaluation/run_evaluation.py
evaluation/run_multiturn_evaluation.py
tests/
characters/
docs/
app/
```

Do not commit:

```text
evaluation/runtime/
evaluation/reports/
data/
```
