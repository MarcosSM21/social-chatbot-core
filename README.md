# social-chatbot-core

Modular project to build, step by step, a chatbot system that can eventually connect to Instagram or similar platforms, read direct messages, generate coherent responses, and evolve toward personalized conversations with context and memory.

## Status (I)

Phase 1 completed: local minimal chatbot.

The project currently provides a fully local chatbot MVP with:

- modular architecture
- local terminal interaction
- configurable bot behavio
- structured chat domain models
- local JSON persistence
- session-based conversation isolation
- recent-history-aware responses
- basic local commands for usability

## Implemented architecture


LocalChannel
   -> ChatOrchestrator
      -> ConversationService
         -> LocalChatRepository
         -> ResponseEngine


##  Status (II)

Phase 2 completed: internal professional API.

The project currently provides:

- a local chatbot mode via terminal
- an internal HTTP API via FastAPI
- a shared modular chat core
- configurable bot behavior
- session-based conversation isolation
- recent-history-aware responses
- local JSON persistence
- API request/response validation

## Implemented architecture


Local mode (terminal)
   -> LocalChannel
      -> ChatOrchestrator
         -> ConversationService
            -> LocalChatRepository
            -> ResponseEngine

API mode (HTTP)
   -> FastAPI endpoint
      -> ChatOrchestrator
         -> ConversationService
            -> LocalChatRepository
            -> ResponseEngine


## Status (III)

Phase 3 completed: real conversational engine with pluggable generation provider.

The project currently provides:

- a local chatbot mode via terminal
- an internal HTTP API via FastAPI
- a shared modular chat core
- configurable bot behavior
- session-based conversation isolation
- recent-history-aware responses
- local JSON persistence
- API request/response validation
- pluggable generation providers
- local LLM support through Ollama
- provider fallback and basic robustness

## Implemented architecture


Local mode (terminal)
   -> LocalChannel
      -> ChatOrchestrator
         -> ConversationService
            -> LocalChatRepository
            -> ResponseEngine
               -> GenerationProvider
                  -> MockGenerationProvider
                  -> LocalLLMGenerationProvider
                  -> FallbackGenerationProvider

API mode (HTTP)
   -> FastAPI endpoint
      -> ChatOrchestrator
         -> ConversationService
            -> LocalChatRepository
            -> ResponseEngine
               -> GenerationProvider
                  -> MockGenerationProvider
                  -> LocalLLMGenerationProvider
                  -> FallbackGenerationProvider

Everything centralized in app/core/container.py