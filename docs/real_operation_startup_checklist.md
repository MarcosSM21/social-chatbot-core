# Real Operation Startup Checklist

This checklist explains how to start the chatbot for real Instagram DM operation.

Use it when you want to run the system locally with a public tunnel and receive real webhook events from Meta.

## 1. Check Environment Variables

Before starting anything, review `.env`.

Minimum relevant variables:

```env
APP_ENV=development
BOT_ENABLED=false
GENERATION_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3
MEMORY_STORAGE_BACKEND=sqlite
SQLITE_DATABASE_PATH=data/social_chatbot.sqlite3
CHARACTER_FILE=characters/laia_ambitious_model.json
WEBHOOK_VERIFY_TOKEN=...
INSTAGRAM_API_VERSION=v25.0
INSTAGRAM_IG_USER_ID=...
INSTAGRAM_ACCESS_TOKEN=...
INSTAGRAM_APP_SECRET=...
INTERNAL_API_KEY=...
```

Recommended initial mode:

```env
BOT_ENABLED=false
```

This captures real DMs without replying.

Only switch to this when you are ready to answer:

```env
BOT_ENABLED=true
```

After changing `.env`, restart FastAPI.

## 2. Start Ollama

In one terminal:

```bash
ollama serve
```

If the model is not available yet:

```bash
ollama pull gemma3
```

Quick check:

```bash
ollama list
```

## 3. Start FastAPI

In another terminal:

```bash
.venv/bin/python -m uvicorn app.api.main:app --reload
```

The API should be available at:

```text
http://localhost:8000
```

Check health:

```bash
curl http://localhost:8000/health
```

## 4. Start Public Tunnel

In another terminal:

```bash
cloudflared tunnel --url http://localhost:8000
```

Copy the generated public HTTPS URL.

Example:

```text
https://example-trycloudflare.com
```

## 5. Configure Meta Webhook Callback

In Meta dashboard, the Instagram webhook callback URL should be:

```text
https://<public-host>/providers/instagram/webhook/messages
```

Example:

```text
https://example-trycloudflare.com/providers/instagram/webhook/messages
```

This same path is used for:

```text
GET  webhook verification
POST real Instagram webhook events
```

The subscribed field should include:

```text
messages
```

## 6. Verify Instagram Subscription

Check subscribed apps:

```bash
curl -G "https://graph.instagram.com/v25.0/${INSTAGRAM_IG_USER_ID}/subscribed_apps" \
  --data-urlencode "access_token=${INSTAGRAM_ACCESS_TOKEN}"
```

Expected result should include:

```json
"subscribed_fields": ["messages"]
```

## 7. Start In Capture-Only Mode

Recommended first run:

```env
BOT_ENABLED=false
```

Send a real DM to the connected Instagram professional account.

Then check operational events:

```bash
curl \
  -H "X-Internal-API-Key: <INTERNAL_API_KEY>" \
  "http://localhost:8000/internal/operations/events?platform=instagram&limit=5"
```

Check summary:

```bash
curl \
  -H "X-Internal-API-Key: <INTERNAL_API_KEY>" \
  "http://localhost:8000/internal/operations/summary?platform=instagram"
```

If the DM appears, webhook reception is working.

## 8. Enable Replies Carefully

When capture-only works, switch:

```env
BOT_ENABLED=true
```

Restart FastAPI.

Recommended safety option:

```env
INSTAGRAM_ALLOWED_USER_IDS=<your-test-user-id>
```

This limits automatic replies to known test users.

If empty:

```env
INSTAGRAM_ALLOWED_USER_IDS=
```

the bot may reply to any user who sends a DM.

## 9. Send Real Test DM

From the allowed Instagram test account, send a simple message:

```text
hola
```

Expected behavior:

```text
Instagram DM
-> webhook POST
-> raw payload stored
-> trace stored
-> conversation processed
-> memory loaded/updated
-> response generated
-> response sent to Instagram
-> outbound trace stored
```

## 10. Inspect Memory

List Instagram memories:

```bash
curl \
  -H "X-Internal-API-Key: <INTERNAL_API_KEY>" \
  "http://localhost:8000/internal/memory/instagram"
```

Inspect one user:

```bash
curl \
  -H "X-Internal-API-Key: <INTERNAL_API_KEY>" \
  "http://localhost:8000/internal/memory/instagram/<external_user_id>"
```

Delete a test memory if needed:

```bash
curl -X DELETE \
  -H "X-Internal-API-Key: <INTERNAL_API_KEY>" \
  "http://localhost:8000/internal/memory/instagram/<external_user_id>"
```

## 11. Run Tests Before Real Use

Before a serious test session:

```bash
.venv/bin/python -m pytest -q
```

## 12. Run Evaluation Before Changing Character Or Model

Single-turn evaluation:

```bash
.venv/bin/python evaluation/run_evaluation.py --provider ollama
```

Multi-turn evaluation:

```bash
.venv/bin/python evaluation/run_multiturn_evaluation.py \
  --provider ollama \
  --character-file characters/laia_ambitious_model.json
```

Evaluation uses:

```text
evaluation/runtime/
```

It does not use real runtime data in:

```text
data/
```

## 13. Common Problems

### Webhook verifies but DMs do not arrive

Check:

```text
- public tunnel is still alive
- Meta callback URL matches the current tunnel
- subscribed field includes messages
- subscribed_apps contains messages
- app is in the correct mode for the sender account
- sender account is allowed/tester if app is not public
```

### Webhook POST arrives but no response is sent

Check:

```text
BOT_ENABLED=true
INSTAGRAM_ALLOWED_USER_IDS
GENERATION_PROVIDER
OLLAMA_BASE_URL
OLLAMA_MODEL
INSTAGRAM_ACCESS_TOKEN
```

### Ollama fails

Check:

```bash
ollama serve
ollama list
```

Also check:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT_SECONDS=60
```

### Internal API returns 401 or 403

Use:

```http
X-Internal-API-Key: <INTERNAL_API_KEY>
```

### Memory looks wrong

Check storage backend:

```env
MEMORY_STORAGE_BACKEND=json
```

or:

```env
MEMORY_STORAGE_BACKEND=sqlite
```

Check the memory document:

```text
docs/data_and_evaluation_storage.md
```

## Safe Default

The safest real-operation sequence is:

```text
1. BOT_ENABLED=false
2. Start Ollama
3. Start FastAPI
4. Start tunnel
5. Verify Meta callback
6. Send test DM
7. Confirm trace was captured
8. Set INSTAGRAM_ALLOWED_USER_IDS
9. BOT_ENABLED=true
10. Restart FastAPI
11. Send another test DM
12. Confirm response and trace
```
