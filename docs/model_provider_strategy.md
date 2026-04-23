# Model Provider Strategy

This document explains how this project thinks about language models, generation providers, runtimes, and future model experimentation.

The goal is to improve model quality and provider flexibility without breaking the current Instagram chatbot architecture.

## Current Goal

The project should be able to compare and eventually use different model backends:

```text
mock provider
Ollama local provider
future Hugging Face local provider
future external API provider
```

The conversational core should not need to know which provider generated the response.

Core flow:

```text
ConversationService
-> ResponseEngine
-> GenerationProvider
-> assistant response text
```

## Important Concepts

### Model

The model is the neural network that generates text.

Examples:

```text
gemma3
llama3.1
mistral
qwen
phi
mistralai/Mistral-7B-Instruct
```

### Provider

The provider is the Python class used by this project to ask for a response.

Examples:

```text
MockGenerationProvider
OllamaGenerationProvider
FallbackGenerationProvider
future HuggingFaceLocalGenerationProvider
future ExternalAPIGenerationProvider
```

### Runtime

The runtime is the system that actually loads and runs the model.

Examples:

```text
Ollama
Hugging Face Transformers
llama.cpp
remote API
```

### Hardware

The hardware is where inference runs.

Examples:

```text
developer laptop
future home miniPC
VPS/cloud server
external provider infrastructure
```

These concepts should stay separate.

Example:

```text
model: gemma3
provider: OllamaGenerationProvider
runtime: Ollama
hardware: local PC
```

Future example:

```text
model: mistralai/Mistral-7B-Instruct
provider: HuggingFaceLocalGenerationProvider
runtime: Hugging Face Transformers
hardware: local PC or future miniPC
```

## Current Providers

### MockGenerationProvider

Purpose:

```text
testing
local development
basic flow validation
```

Pros:

```text
fast
deterministic
no external services
no model download
safe for tests
```

Cons:

```text
not useful for judging conversational quality
does not really follow character voice
does not truly reason over memory
```

Use when:

```text
checking code flow
running tests
generating quick evaluation reports
```

### OllamaGenerationProvider

Current meaning:

```text
Ollama-backed local LLM provider
```

Even though the name is generic, today this provider talks to:

```text
OLLAMA_BASE_URL=http://localhost:11434
```

Pros:

```text
simple local model usage
no paid LLM API
good fit for privacy-first experiments
compatible with future self-hosted miniPC direction
```

Cons:

```text
depends on Ollama running
model availability depends on Ollama
performance depends on local hardware
less control than loading models directly with Python
```

Use when:

```text
testing real conversation quality locally
running Instagram bot with local model
comparing local Ollama models
```

### FallbackGenerationProvider

Purpose:

```text
try primary provider
fallback to another provider if primary fails
```

Current use:

```text
Ollama -> Mock
```

Pros:

```text
prevents total failure when primary provider is unavailable
useful in development
```

Cons:

```text
can hide real provider failures
mock fallback may produce low-quality responses
should be used carefully in real operation
```

Use when:

```text
development robustness matters more than strict quality
```

Avoid or review carefully when:

```text
running real user-facing conversations
```

## Future Providers

### HuggingFaceLocalGenerationProvider

Possible future provider that loads models through Python libraries.

Potential runtime:

```text
Hugging Face Transformers
```

Possible dependencies:

```text
torch
transformers
accelerate
safetensors
sentencepiece
```

Pros:

```text
access to many Hugging Face models
more control over model loading
more control over generation parameters
good learning path for local inference
compatible with future miniPC/server experiments
```

Cons:

```text
heavy dependencies
model downloads can be large
CPU inference can be slow
GPU support adds complexity
tests must not download models
can make the project harder to install if not optional
```

Implementation principle:

```text
optional and experimental
```

The base project should still run without installing heavy Hugging Face dependencies.

### ExternalAPIGenerationProvider

Possible future provider that calls a hosted model API.

Pros:

```text
high model quality
fast responses
no local GPU required
easier deployment on cheap server
```

Cons:

```text
paid API usage
less privacy
provider dependency
network dependency
possible model behavior changes outside our control
```

Use when:

```text
we want stable 24/7 deployment without hosting a model ourselves
we want to compare local models with stronger hosted models
```

## Hugging Face Vs Ollama

### Ollama

Ollama is a convenient local model runtime.

Project flow:

```text
Python app
-> HTTP request
-> Ollama
-> model response
```

Best for:

```text
simple local model experiments
running models without managing Transformers code
privacy-first local workflows
future miniPC experiments
```

### Hugging Face Local

Hugging Face local inference means the Python app loads the model more directly.

Possible project flow:

```text
Python app
-> transformers pipeline/model
-> local model files
-> model response
```

Best for:

```text
learning direct model loading
testing models not available in Ollama
controlling tokenizer/model/generation settings
eventual custom inference experiments
```

## Future Configuration Ideas

Current relevant configuration:

```env
GENERATION_PROVIDER=mock
GENERATION_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3
ENABLE_PROVIDER_FALLBACK=true
```

Possible future Hugging Face configuration:

```env
GENERATION_PROVIDER=huggingface_local
HUGGINGFACE_MODEL_ID=
HUGGINGFACE_DEVICE=cpu
HUGGINGFACE_MAX_NEW_TOKENS=150
HUGGINGFACE_TEMPERATURE=0.7
```

These variables should not be added blindly until the provider exists.

## Testing Rules

Automated tests should not:

```text
download Hugging Face models
call remote LLM APIs
require Ollama to be running
require a GPU
```

Provider tests should use:

```text
mocks
fake responses
dependency injection
small unit tests
```

Manual evaluations can use:

```text
Ollama
future Hugging Face models
future external APIs
```

## Evaluation Criteria

When comparing providers/models, evaluate:

```text
naturalness
shortness
character consistency
memory usage
safety
latency
stability
resource usage
setup complexity
privacy
cost
```

Pass/fail is not enough for model quality.

Markdown reports should be read manually when judging:

```text
style
personality
conversation flow
human realism
```

## Self-Hosted Direction

The long-term strategic direction is local-first and self-hosting friendly.

Future target:

```text
home miniPC
-> FastAPI
-> Ollama or another local runtime
-> local database
-> Cloudflare Tunnel
-> Instagram/X/etc. integrations
```

This does not mean every next step must be infrastructure work.

Current principle:

```text
Improve the chatbot now, but keep the architecture compatible with future self-hosted deployment.
```

## Near-Term Plan

Recommended Phase 20 direction:

```text
1. Document model/provider strategy
2. Improve evaluation metadata for model comparisons
3. Clarify or rename the current Ollama provider
4. Design HuggingFaceLocalGenerationProvider
5. Optionally implement an experimental Hugging Face provider
6. Compare model quality through existing evaluation reports
```

The project should move toward provider flexibility without making the default setup heavy or fragile.
