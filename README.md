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


## status (IV)

Phase 4 completed: external channel preparation and webhook-ready integration design.

The project currently provides:

- a local chatbot mode via terminal
- an internal HTTP API via FastAPI
- a shared modular chat core
- configurable bot behavior
- session-based conversation isolation
- local JSON persistence
- pluggable generation providers
- local LLM support through Ollama
- provider fallback and basic robustness
- explicit external message event modeling
- webhook-ready HTTP entrypoint
- external-to-internal conversation mapping

## Implemented architecture

Local mode (terminal)
   -> LocalChannel
      -> ChatOrchestrator
         -> ConversationService
            -> LocalChatRepository
            -> ResponseEngine
               -> GenerationProvider

API mode (simple internal)
   -> /messages
   -> ExternalMessageEvent
   -> HttpChannelAdapter
      -> ChatOrchestrator
         -> ConversationService
            -> LocalChatRepository
            -> ResponseEngine
               -> GenerationProvider

Webhook-ready mode
   -> /webhook/messages
   -> ExternalMessageEvent
   -> HttpChannelAdapter
      -> ConversationMappingRepository
      -> ChatOrchestrator
         -> ConversationService
            -> LocalChatRepository
            -> ResponseEngine
               -> GenerationProvider


## status(V)

Phase 5 completed: platform-ready webhook flow and outbound channel preparation.

The project currently provides:

- a local chatbot mode via terminal
- an internal HTTP API via FastAPI
- a shared modular chat core
- configurable bot behavior
- local JSON persistence
- pluggable generation providers
- local LLM support through Ollama
- provider fallback and robustness
- explicit external message event modeling
- webhook verification flow
- platform payload parsing and filtering
- external-to-internal conversation mapping
- outbound channel message preparation

## Implemented architecture

Webhook verification
   -> GET /webhook/verify

Platform incoming flow
   -> POST /webhook/messages
   -> PlatformWebhookPayload
   -> PlatformInboundService
      -> PlatformPayloadParser
      -> HttpChannelAdapter
         -> ConversationMappingRepository
         -> ChatOrchestrator
            -> ConversationService
               -> LocalChatRepository
               -> ResponseEngine
                  -> GenerationProvider

Outbound preparation
   -> HttpChannelResult
      -> ChatTurn
      -> OutboundChannelMessage


## status (VI)

Phase 6 completed: provider-specific integration architecture and outbound preparation.

The project currently provides:

- a local chatbot mode via terminal
- an internal HTTP API via FastAPI
- a shared modular chat core
- configurable bot behavior
- local JSON persistence
- pluggable generation providers
- local LLM support through Ollama
- provider fallback and robustness
- platform-ready webhook flow
- provider-specific payload parsing
- provider-specific event filtering
- outbound sender abstraction
- external trace persistence for processed platform messages

## Implemented architecture

Provider-specific incoming flow
   -> /providers/instagram/webhook/messages
   -> InstagramWebhookPayload
   -> InstagramPayloadParser
      -> ProviderPayloadParseResult
   -> PlatformWebhookPayload
   -> PlatformInboundService
      -> PlatformPayloadParser
         -> PayloadParseResult
      -> HttpChannelAdapter
         -> ConversationMappingRepository
         -> ChatOrchestrator
            -> ConversationService
               -> LocalChatRepository
               -> ResponseEngine
                  -> GenerationProvider
      -> OutboundSender
         -> OutboundSendResult
      -> ExternalTraceRepository

