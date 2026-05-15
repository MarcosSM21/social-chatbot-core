# social-chatbot-core

Local-first conversational runtime built with FastAPI and Ollama.

This project explores how to move from a simple prompt-driven chatbot to a more disciplined runtime with:

- pluggable generation providers
- session-aware conversation handling
- lightweight user memory
- channel-ready inbound/outbound flow
- queue-aware generation control
- delayed outbound delivery
- internal observability for live runtime state

It is designed for controlled real-world experimentation, not for industrial-scale deployment.

## What It Does

At a high level, `social-chatbot-core` lets you:

- run a local conversational backend with FastAPI
- use local LLMs through Ollama
- persist chat turns and user memory
- process external-style message events
- delay outbound replies intentionally
- inspect runtime queues, pending outbound messages, and conversation state through internal dashboards

The project is channel-oriented and currently includes an Instagram-style runtime path, but the reusable value of the repo is the runtime architecture itself rather than any single persona or use case.

## Core Capabilities

### Conversation core

- modular conversation service
- recent-turn context
- pluggable character definitions
- persistent chat history
- configurable generation provider

### Memory

- persistent user memory
- working memory buffer
- memory safety validation
- SQLite-backed storage support

### Runtime control

- per-conversation sequencing
- in-flight conversation locking
- global generation concurrency control
- delayed outbound scheduling
- safe file-backed repository writes

### Observability

- operational traces
- internal runtime summary endpoints
- per-conversation runtime inspection
- pending outbound inspection
- HTML dashboard for internal monitoring

## Architecture Snapshot

```text
Inbound event
-> bundle / queue / sequencing
-> conversation processing
   -> memory load
   -> prompt/context build
   -> generation provider
   -> safety / cleanup
   -> chat turn persistence
-> pending outbound storage
-> delayed outbound scheduler
-> final send
```

## Main Components

```text
app/api/
   FastAPI routes, internal tooling, runtime dashboard

app/services/
   conversation logic, context building, safety, language routing

app/storage/
   chat history, traces, mappings, pending outbound, SQLite memory

app/outbound/
   outbound sender logic

app/channels/
   inbound parsing and channel-facing adapters

characters/
   pluggable character JSON definitions
```

## Public Character Set

The repo includes a small public character set that is useful for demos, evaluation, and experimentation:

- `support_concierge`
- `sales_qualifier`
- `community_manager`
- `appointment_assistant`

These characters are intentionally generic and reusable. They are meant to demonstrate how the runtime can swap conversational identity without changing the core orchestration layer.

## Behavior Profiles

The runtime separates character identity from channel behavior.

Two useful concepts:

- `CHARACTER_FILE`
  chooses the active conversational persona
- `INSTAGRAM_BEHAVIOR_PROFILE`
  chooses how Instagram-specific behavior should work

Current public profile options:

- `neutral`
  no forced redirect behavior; Instagram replies are treated like normal channel replies
- `redirecting_dm`
  enables trigger-based redirect behavior for experimental DM funnels

Example:

```env
CHARACTER_FILE=characters/support_concierge.json
INSTAGRAM_BEHAVIOR_PROFILE=neutral
INSTAGRAM_REDIRECT_URL=https://example.com/private
```

## Internal Observability

The project includes internal endpoints and a lightweight dashboard to understand live runtime state.

Useful runtime endpoints:

- `GET /internal/operations/events`
- `GET /internal/operations/summary`
- `GET /internal/instagram/runtime/summary`
- `GET /internal/instagram/runtime/conversations`
- `GET /internal/instagram/runtime/conversations/{external_user_id}`
- `GET /internal/instagram/runtime/pending-outbound`
- `GET /internal/instagram/runtime/dashboard`

These are intended for controlled testing and operator visibility, not for public exposure.

## Quickstart

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create your environment file

```bash
cp .env.example .env
```

Runtime data is created locally under `data/` and is intentionally ignored by git.

### 3. Choose a generation provider

For Ollama-based local inference:

```env
GENERATION_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3
```

### 4. Start Ollama separately

Example:

```bash
ollama serve
```

### 5. Run the API

```bash
uvicorn app.api.main:app --reload
```

### 6. Open the docs

```text
http://127.0.0.1:8000/docs
```

### 7. Open the runtime dashboard

```text
http://127.0.0.1:8000/internal/instagram/runtime/dashboard
```

Use your internal API key inside the dashboard to inspect:

- runtime summary
- conversation list
- per-conversation detail
- pending outbound state

## Minimal Internal Test

You can test the conversation core without any external channel by calling the internal message endpoint.

```bash
curl -X POST http://127.0.0.1:8000/internal/messages \
  -H "Content-Type: application/json" \
  -H "X-Internal-API-Key: dev-internal-api-key" \
  -d '{
    "session_id": "local-test-1",
    "message": "hello"
  }'
```

## Current Boundaries

This project already supports controlled runtime experimentation, but the current public version still has deliberate limits:

- single-process runtime assumptions
- process-local locks rather than distributed coordination
- outbound delay persistence, but not full inbound job persistence
- controlled rollout suitability, not industrial scaling
- internal dashboards intended for operators, not end users

## Good First Things To Try

- switch `CHARACTER_FILE` between the bundled public characters
- run with `GENERATION_PROVIDER=mock` first, then move to `ollama`
- keep `INSTAGRAM_BEHAVIOR_PROFILE=neutral` unless you explicitly want redirect-style DM behavior
- use the internal dashboard before exposing any external webhook flow

## Status

The project is now in a public-friendly V1 state focused on the reusable runtime:

- local-first generation through Ollama
- persistent memory and chat history
- queue-aware runtime control
- delayed outbound delivery
- internal observability for controlled testing and rollout

## License / Notes

No public license has been added yet in this version of the repo.

Before publishing broadly, review:

- credentials and token hygiene
- test fixtures that may be too tied to private experimentation
