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


## Status (VII)

Phase 1 completed: conversational context consolidation.

This phase does not add memory yet. Its goal is to professionalize the core so style, memory, and safety can be added later without mixing concerns inside the LLM providers.

The project now provides:

- real Instagram DM capture and reply flow
- raw provider payload persistence
- external trace persistence for inbound and outbound flow
- explicit `ConversationContext` modeling
- `ConversationContextBuilder` as the single place where conversational context is assembled
- separation between:
  - system instructions
  - style instructions
  - recent history
  - future memory slots
- generation providers that consume a full context instead of building it ad hoc
- reserved slots for future per-user memory:
  - `user_profile`
  - `conversation_summary`

## Implemented architecture

Instagram DM flow
   -> GET/POST /providers/instagram/webhook/messages
   -> InstagramWebhookPayload
   -> InstagramPayloadParser
      -> ProviderPayloadParseResult
      -> ExternalMessageEvent
   -> HttpChannelAdapter
      -> ConversationMappingRepository
      -> ChatOrchestrator
         -> ConversationService
            -> LocalChatRepository
            -> ConversationContextBuilder
               -> ConversationContext
                  -> current_message
                  -> recent_history
                  -> system_instructions
                  -> style_instructions
                  -> user_profile (empty for now)
                  -> conversation_summary (empty for now)
            -> ResponseEngine
               -> GenerationProvider
                  -> MockGenerationProvider
                  -> LocalLLMGenerationProvider
                  -> FallbackGenerationProvider
   -> InstagramOutboundSender
   -> ExternalTraceRepository
The main architectural gain of this phase is that the system no longer asks each provider to invent its own conversational context. The core now builds that context explicitly, which makes the next phase predictable: adding real per-user memory without distorting the Instagram flow or the provider layer.


## Status (VIII)

Phase 2 completed: per-user memory foundations.

This phase introduces a first real memory layer on top of the conversational core. The system no longer depends only on recent turns: it can now persist simple memory per external user, load it into the conversation context, update it after each turn, and expose its usage through operational traces.

The project now provides:

- explicit `UserMemory` modeling per platform and external user
- dedicated `UserMemoryRepository` persistence in `data/user_memories.json`
- separation between:
  - raw chat history
  - stable user profile
  - rolling conversation summary
- memory-aware context building through `ConversationContextBuilder`
- memory loading before generation
- memory updating after generation
- basic memory usage traceability with:
  - `memory_loaded`
  - `memory_updated`

## Implemented architecture

Instagram DM flow with memory
   -> GET/POST /providers/instagram/webhook/messages
   -> InstagramWebhookPayload
   -> InstagramPayloadParser
      -> ProviderPayloadParseResult
      -> ExternalMessageEvent
   -> HttpChannelAdapter
      -> ConversationMappingRepository
      -> ChatOrchestrator
         -> ConversationService
            -> LocalChatRepository
            -> UserMemoryRepository
               -> UserMemory
                  -> user_profile
                  -> conversation_summary
                  -> updated_at
            -> ConversationContextBuilder
               -> ConversationContext
                  -> current_message
                  -> recent_history
                  -> system_instructions
                  -> style_instructions
                  -> user_profile
                  -> conversation_summary
            -> ResponseEngine
               -> GenerationProvider
         -> ChatTurn
            -> session_metadata
               -> memory_loaded
               -> memory_updated
   -> InstagramOutboundSender
   -> ExternalTraceRepository

At this stage, memory is intentionally simple and controlled. The profile is updated through basic explicit-user-signal rules, and the conversation summary is kept as a compact rolling summary of recent exchanges. The goal of this phase is not perfect memory, but to establish a clean, inspectable foundation for personalization.


## Status (IX)

Phase 3 completed: configurable conversational style.

This phase turns style from a loose prompt fragment into a first-class part of the conversational core. The system can now build an explicit style object, derive prompt instructions from it, choose a style preset, override style attributes through settings, and expose the effective style in traces.

The project now provides:

- explicit `ConversationStyle` modeling
- reusable style presets such as:
  - `short_direct_calm`
  - `warm_supportive`
  - `formal_clear`
- style construction through `ConversationContextBuilder`
- separation between:
  - style attributes
  - style rules
  - system instructions
- preset-based style defaults with optional per-attribute overrides from settings
- style traceability through:
  - `style_preset`
  - `style_snapshot`

## Implemented architecture

Conversational style flow
   -> Settings
      -> style_preset
      -> optional style overrides
   -> ConversationContextBuilder
      -> ConversationStyle.from_preset(...)
      -> per-field override merge
      -> style rules
      -> style_instructions
   -> ConversationContext
      -> style
      -> style_instructions
   -> ResponseEngine
      -> GenerationProvider
   -> ChatTurn
      -> session_metadata
         -> style_preset
         -> style_snapshot
   -> ExternalTraceRepository
      -> ExternalTraceRecord
         -> style_preset
         -> style_snapshot

The main gain of this phase is controllability. Style is no longer trapped inside ad hoc prompt text: it is now configurable, inspectable, and traceable across the full Instagram conversation flow.


## Status (X)

Phase 4 completed: conversational safety foundations.

This phase introduces a first safety layer around the conversational core. The goal is not to build a complete moderation system yet, but to make safety explicit, visible, and active in the most important places: the context sent to the model, the response before it is sent to Instagram, and the memory before it is persisted.

The project now provides:

- explicit `ConversationSafetyPolicy` modeling
- safety instructions injected into `ConversationContext`
- provider prompt ordering with:
  - system instructions
  - safety instructions
  - style instructions
  - memory
  - recent history
  - current message
- assistant response safety validation before persistence and outbound send
- fallback safe responses for empty or sensitive assistant output
- user memory safety validation before profile or summary persistence
- safety traceability through:
  - `safety_policy_active`
  - `safety_snapshot`
  - `safety_validation_status`
  - `safety_validation_detail`
  - `safety_matched_rule`
  - `memory_profile_status`
  - `memory_summary_status`

## Implemented architecture

Conversational safety flow
   -> ConversationContextBuilder
      -> ConversationSafetyPolicy.default()
      -> safety_instructions
   -> ConversationContext
      -> safety_policy
      -> safety_instructions
   -> LocalLLMGenerationProvider
      -> system prompt includes safety before style and memory
   -> ConversationService
      -> AssistantResponseSafetyValidator
         -> passed | adjusted | blocked
      -> UserMemorySafetyValidator
         -> memory profile validation
         -> memory summary validation
      -> ChatTurn
         -> session_metadata
            -> safety snapshot
            -> response safety result
            -> memory safety result
   -> ExternalTraceRepository
      -> ExternalTraceRecord
         -> safety and memory-safety fields

The main gain of this phase is operational safety. The chatbot now has explicit guardrails against leaking secrets or internal instructions, and it avoids storing obvious sensitive data in long-term memory. This is still a lightweight safety layer, but it is now part of the core flow instead of being hidden inside a generic prompt.


## Status (XI)

Phase 6 completed: operational robustness foundations.

This phase improves the reliability of the Instagram DM flow before adding more intelligence to the chatbot. The goal was to make failures explicit, traceable, and safe enough for the system to keep running without blindly crashing on provider or sender errors.

The project now provides:

- webhook protection when the conversational core or generation provider fails
- controlled handling of unexpected Instagram outbound sender exceptions
- structured operational trace fields:
  - `operational_status`
  - `operational_error_type`
  - `operational_detail`
- direct tests for `InstagramOutboundSender` without real network calls
- webhook tests for:
  - valid signature
  - invalid signature
  - valid Instagram DM payload
  - ignored non-text payload
  - duplicate provider message
  - generation provider failure
  - unexpected outbound sender failure
- regression coverage across parser, memory, safety, webhook and outbound sender

## Implemented architecture

Operationally robust Instagram flow

   -> GET/POST /providers/instagram/webhook/messages
   -> signature validation
   -> raw payload persistence
   -> InstagramPayloadParser
      -> ProviderPayloadParseResult
      -> ExternalMessageEvent
   -> duplicate detection by provider_message_id
   -> HttpChannelAdapter
      -> ConversationService
         -> ConversationContextBuilder
         -> ResponseEngine
         -> AssistantResponseSafetyValidator
         -> UserMemorySafetyValidator
   -> InstagramOutboundSender
      -> OutboundSendResult
         -> sent | failed
   -> ExternalTraceRepository
      -> ExternalTraceRecord
         -> inbound_status
         -> outbound_status
         -> operational_status
         -> operational_error_type
         -> operational_detail
         -> memory trace fields
         -> style trace fields
         -> safety trace fields

At this stage, the bot is not only able to receive and reply to real Instagram DMs; it also has a first operational safety net. If generation fails, the webhook records the failure instead of retrying blindly. If outbound sending fails, the result is persisted as a failed send. This gives the next phase a safer foundation for evaluating and tuning the actual LLM behavior.
