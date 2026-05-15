import hashlib
import hmac
import json
import time
import asyncio
import os
from collections import deque
from dotenv import load_dotenv
import random 
import uuid
from contextlib import asynccontextmanager


from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app.api.schemas import (
    MessageRequest,
    MessageResponse,
    HealthResponse,
    InfoResponse,
    WebhookMessageRequest,
    WebhookEventResponse,
    InstagramWebhookPayloadRequest,
    UserMemoryResponse,
    UserMemoryListResponse,
    UserMemoryDeleteResponse,
    UserMemoryCleanupResponse,
    OperationalEventListResponse,
    OperationalEventResponse,
    OperationalSummaryResponse,
    CharacterListResponse,
    CharacterSummaryResponse,
    ActiveCharacterResponse,
    InstagramBlockedUserResponse,
    InstagramGuardrailsSummaryResponse,
    InstagramGuardrailActionResponse,
    InstagramUserResetResponse,
    InstagramRuntimeSummaryResponse,
    InstagramRuntimeConversationResponse,
    InstagramRuntimeConversationListResponse,
    InstagramRuntimePendingOutboundResponse,
    InstagramRuntimeTurnResponse,
    InstagramRuntimeTraceResponse,
    InstagramRuntimeConversationDetailResponse,
    InstagramPendingOutboundRecordResponse,
    InstagramPendingOutboundListResponse,
)

from app.channels.http_channel_result import HttpChannelResult
from app.channels.instagram_payload_parser import InstagramPayloadParser
from app.channels.provider_parser_result import ProviderPayloadParseResult
from app.models.provider_payloads import InstagramWebhookPayload


from app.core.settings import Settings
from app.models.external import ExternalMessageEvent
from app.core.container import (
    build_http_channel_adapter, 
    build_platform_inbound_service,
    build_user_memory_repository,
)
from app.models.platform_payload import PlatformWebhookPayload
from app.providers.exceptions import GenerationProviderError
from app.storage.external_trace_repository import ExternalTraceRepository
from app.models.external_trace import ExternalTraceRecord
from app.models.provider_raw_payload import ProviderRawPayloadRecord
from app.storage.provider_raw_payload_repository import ProviderRawPayloadRepository
from app.outbound.instagram_sender import InstagramOutboundSender
from app.outbound.result import OutboundSendResult
from app.storage.character_repository import CharacterRepository
from app.models.instagram_bundle import  PendingInstagramBundle
from app.storage.instagram_admission_repository import InstagramAdmissionRepository
from app.storage.instagram_turn_budget_repository import InstagramTurnBudgetRepository
from app.storage.conversation_mapping_repository import ConversationMappingRepository
from app.storage.local_chat_repository import LocalChatRepository
from app.services.language_routing import detect_conversation_language
from app.models.pending_outbound import PendingOutboundMessage
from app.storage.pending_outbound_repository import PendingOutboundRepository








load_dotenv()



@asynccontextmanager
async def lifespan(app: FastAPI):
    global _instagram_outbound_scheduler_task
    global _instagram_generation_dispatch_task

    for bundle_key in instagram_pending_outbound_repository.list_pending_bundle_keys():
        _instagram_pending_send_bundle_keys.add(bundle_key)

    _instagram_outbound_scheduler_task = asyncio.create_task(
        _instagram_outbound_scheduler_loop()
    )

    try:
        yield
    finally:
        if _instagram_outbound_scheduler_task is not None:
            _instagram_outbound_scheduler_task.cancel()

            try:
                await _instagram_outbound_scheduler_task
            except asyncio.CancelledError:
                pass

            _instagram_outbound_scheduler_task = None

        if _instagram_generation_dispatch_task is not None:
            _instagram_generation_dispatch_task.cancel()

            try:
                await _instagram_generation_dispatch_task
            except asyncio.CancelledError:
                pass

            _instagram_generation_dispatch_task = None



app = FastAPI(
    title="social-chatbot-core API",
    version="0.1.0",
    description="Interanl API para el chatbot social core project",
    lifespan=lifespan,
)

settings = Settings.from_env()
_instagram_last_reply_by_user: dict[str, float] = {}
_instagram_pending_bundles: dict[str, PendingInstagramBundle] = {}
_instagram_deferred_bundles: dict[str, PendingInstagramBundle] = {}
_instagram_ready_bundles: dict[str, PendingInstagramBundle] = {}
_instagram_bundle_tasks: dict[str, asyncio.Task] = {}
_instagram_inflight_bundle_keys: set[str] = set()
_instagram_pending_send_bundle_keys: set[str] = set()
_instagram_ready_bundle_queue: deque[str] = deque()
_instagram_ready_bundle_keys: set[str] = set()
_instagram_buffered_message_ids: set[str] = set()
_instagram_outbound_scheduler_task: asyncio.Task | None = None
_instagram_generation_dispatch_task: asyncio.Task | None = None
_instagram_active_generation_count = 0


instagram_admission_repository = InstagramAdmissionRepository(
    settings.instagram_admitted_users_path
)
instagram_turn_budget_repository = InstagramTurnBudgetRepository(
    settings.instagram_blocked_users_path
)
instagram_pending_outbound_repository = PendingOutboundRepository(
    settings.instagram_pending_outbound_path
)



###### RUTAS AUXILIARES ##########
@app.get("/")
def root() -> dict:
    return {
        "message": "social-chatbot-core API is running",
        "docs_url": "/docs",
        "health_url": "/health",
        "info_url": "/info",
        "privacy_policy_url": "/privacy-policy",
        "internal_messages_url": "/internal/messages",
        "generic_webhook_verify_url": "/webhooks/verify",
        "generic_webhook_messages_url": "/webhooks/messages",
        "instagram_webhook_verify_url": "/providers/instagram/webhook/verify",
        "instagram_webhook_messages_url": "/providers/instagram/webhook/messages",
    }

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")

@app.get("/info", response_model=InfoResponse)
def info() -> InfoResponse:
    return InfoResponse(
        service_name="social-chatbot-core",
        version="0.1.0",
        enviroment=settings.app_env,
        llm_provider=settings.llm_provider
    )
@app.get("/privacy-policy", response_class=HTMLResponse)
def privacy_policy() -> HTMLResponse:
    html = """
    <!DOCTYPE html>
    <html lang="es">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Politica de Privacidad | social-chatbot-core</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            background: #f7f7f5;
            color: #1f2937;
            margin: 0;
            padding: 40px 20px;
          }
          main {
            max-width: 760px;
            margin: 0 auto;
            background: #ffffff;
            padding: 32px;
            border-radius: 16px;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
          }
          h1, h2 {
            color: #111827;
          }
          p, li {
            line-height: 1.6;
          }
          ul {
            padding-left: 20px;
          }
          .note {
            margin-top: 24px;
            padding: 16px;
            background: #fef3c7;
            border-radius: 12px;
          }
          .conversation-item.pending_send {
            border-color: #e8b9b9;
            background: #fff1f1;
            }

            .conversation-item.inflight {
            border-color: #ead9a2;
            background: #fff9e7;
            }

            .conversation-item.ready {
            border-color: #bfd8c6;
            background: #f3fbf5;
            }

            .conversation-item.deferred {
            border-color: #d8c8ea;
            background: #f8f2ff;
            }

            .conversation-item.pending_bundle {
            border-color: #c8d7ea;
            background: #f1f7ff;
            }

            .conversation-item.idle {
            border-color: #e2d8cc;
            background: #fcfaf7;
            }
        </style>
      </head>
      <body>
        <main>
          <h1>Politica de Privacidad</h1>
          <p>
            Esta es una pagina provisional de politica de privacidad para
            <strong>social-chatbot-core</strong>.
          </p>

          <h2>Datos que pueden tratarse</h2>
          <ul>
            <li>Mensajes enviados por usuarios a traves de canales conectados.</li>
            <li>Identificadores tecnicos de conversacion y plataforma.</li>
            <li>Registros tecnicos necesarios para depuracion y trazabilidad.</li>
          </ul>

          <h2>Finalidad</h2>
          <p>
            Los datos se utilizan exclusivamente para pruebas tecnicas,
            integraciones de mensajeria, procesamiento conversacional y
            seguimiento operativo del sistema.
          </p>

          <h2>Conservacion</h2>
          <p>
            Durante esta fase de desarrollo, algunos datos pueden almacenarse
            temporalmente en registros locales con fines de prueba.
          </p>

          <h2>Contacto</h2>
          <p>
            Si necesitas una version formal o definitiva de esta politica,
            sustituye este contenido por la informacion legal real del proyecto
            antes de usarlo en produccion.
          </p>

          <div class="note">
            Este documento es un mockup tecnico para desarrollo y configuracion
            inicial de integraciones.
          </div>
        </main>
      </body>
    </html>
    """
    return HTMLResponse(content=html)

###########################################
############### SAFETY INTERNO################

def require_internal_api_key(x_internal_api_key: str | None = Header(default=None, alias="X-Internal-API-Key")) -> None:
    if x_internal_api_key != settings.internal_api_key:
        raise HTTPException(status_code=403, detail="Invalid internal API key")


########### MENSAJES INTERNOS  ########################

@app.post("/internal/messages", response_model=MessageResponse)
def create_internal_message(request: MessageRequest, _: None = Depends(require_internal_api_key)) -> MessageResponse:
    
    event = ExternalMessageEvent(
        platform="api",
        conversation_id=request.session_id,
        user_id="api-user",
        message_text=request.message,
        channel_metadata={
            "source": "internal_api"
        }
    )
    
    http_channel_adapter = build_http_channel_adapter(settings)


    try:
        channel_result = http_channel_adapter.process_event(event)
    except GenerationProviderError as exc:
        raise HTTPException(status_code=503, detail=f"Generation provider error: {exc}") from exc

    return MessageResponse(
        user_message=channel_result.turn.user_message.content,
        assistant_message=channel_result.turn.assistant_message.content,
        session_id=channel_result.turn.session_id
    )

@app.post("/internal/messages/bundled", response_model=WebhookEventResponse)
async def create_internal_bundled_message(
    request: MessageRequest,
    _: None = Depends(require_internal_api_key),
) -> WebhookEventResponse:
    event = ExternalMessageEvent(
        platform="api",
        conversation_id=request.session_id,
        user_id="api-user",
        message_text=request.message,
        channel_metadata={
            "source": "internal_api_bundled",
        },
    )

    enqueue_status = _enqueue_instagram_event(event)

    if enqueue_status == "duplicate_buffered":
        return WebhookEventResponse(
            status="ignored",
            detail="Duplicate buffered internal message ignored.",
        )

    return WebhookEventResponse(
        status="accepted",
        detail="Internal message buffered for bundling.",
    )


##############################################################


################# MEMORIA INTERNA #####################################


@app.delete("/internal/memory/empty", response_model=UserMemoryCleanupResponse)
def delete_empty_internal_memories(_: None = Depends(require_internal_api_key)) -> UserMemoryCleanupResponse:
    memory_repository = build_user_memory_repository(settings)
    deleted_count = memory_repository.delete_empty_memories()

    return UserMemoryCleanupResponse(
        deleted_count=deleted_count,
        detail = f"Deleted {deleted_count} empty user memory record(s)"
    )


@app.get("/internal/memory/{platform}", response_model=UserMemoryListResponse)
def list_internal_memory_by_platform(platform: str,_: None = Depends(require_internal_api_key)) -> UserMemoryListResponse:
    memory_repository = build_user_memory_repository(settings)
    memories = memory_repository.list_by_platform(platform)

    memory_responses = [_to_user_memory_response(memory) for memory in memories]

    return UserMemoryListResponse(
        platform=platform,
        count = len(memory_responses),
        memories = memory_responses
    )

@app.get("/internal/memory/{platform}/{external_user_id}", response_model=UserMemoryResponse)
def get_internal_memory_by_user(platform: str, external_user_id: str,_: None = Depends(require_internal_api_key)) -> UserMemoryResponse:
    memory_repository = build_user_memory_repository(settings)
    memory = memory_repository.get_by_user(platform=platform, external_user_id=external_user_id)

    if memory is None:
        raise HTTPException(status_code=404, detail="User memory not found")
    
    return _to_user_memory_response(memory)


@app.delete("/internal/memory/{platform}/{external_user_id}", response_model=UserMemoryDeleteResponse)
def delete_internal_memory_by_user( platform: str, external_user_id: str, _: None = Depends(require_internal_api_key)) -> UserMemoryDeleteResponse:
    memory_repository = build_user_memory_repository(settings)
    deleted = memory_repository.delete_by_user( platform=platform, external_user_id=external_user_id)

    if not deleted: 
        raise HTTPException(status_code=404, detail="User memory not found")
    
    return UserMemoryDeleteResponse(
        platform=platform,
        external_user_id=external_user_id,
        deleted=True,
        detail="User memory deleted",
    )


########################## PERSONAJES INTERNOS ##############################


@app.get("/internal/characters", response_model=CharacterListResponse)
def list_internal_characters(_:None = Depends(require_internal_api_key)) -> CharacterListResponse:
    character_repository = CharacterRepository()
    characters = character_repository.list_characters()

    character_responses = [
        CharacterSummaryResponse(
            character_id=character.character_id,
            display_name=character.display_name,
            file_path=character.file_path,
        )
        for character in characters
    ]

    return CharacterListResponse(
        count=len(character_responses),
        characters=character_responses
    )


@app.get("/internal/characters/active", response_model=ActiveCharacterResponse)
def get_active_internal_character(_:None = Depends(require_internal_api_key)) -> ActiveCharacterResponse:
    character_repository = CharacterRepository()
    result = character_repository.load_by_file_path_with_status(settings.character_file)

    is_default =result.character.character_id == "default"

    return ActiveCharacterResponse(
        character_id=result.character.character_id,
        display_name=result.character.display_name,
        file_path=None if is_default else settings.character_file,
        is_default=is_default,
        load_status=result.status,
        load_detail=result.detail,
    )

############################################################################


########################### OPERACION INTERNA ##############################

@app.get("/internal/operations/events", response_model=OperationalEventListResponse)
def list_recent_operational_events(
    limit: int = Query(default=20, ge=1, le=100),
    platform: str | None = None,
    _: None = Depends(require_internal_api_key),
) -> OperationalEventListResponse:
    
    trace_repository = ExternalTraceRepository(settings.external_traces_path)
    records = trace_repository.list_recent_records(
        limit=limit,
        platform=platform,
    )

    events = [_to_operational_event_response(record) for record in records]

    return OperationalEventListResponse(
        count =len(events),
        events=events
    )


@app.get("/internal/operations/summary", response_model=OperationalSummaryResponse)
def get_operational_summary(platform: str | None = None, _: None = Depends(require_internal_api_key)) -> OperationalSummaryResponse:
    trace_repository = ExternalTraceRepository(settings.external_traces_path)
    summary = trace_repository.summarize_records(platform=platform)

    return OperationalSummaryResponse(
        platform=summary["platform"],
        total=summary["total"],
        inbound_status_counts=summary["inbound_status_counts"],
        outbound_status_counts=summary["outbound_status_counts"],
        operational_status_counts=summary["operational_status_counts"],
        operational_error_type_counts=summary["operational_error_type_counts"],
    )


@app.get("/internal/instagram/guardrails/summary", response_model=InstagramGuardrailsSummaryResponse)
def get_instagram_guardrails_summary(_: None = Depends(require_internal_api_key)) -> InstagramGuardrailsSummaryResponse:
    admitted_users = instagram_admission_repository.list_user_ids()
    blocked_data = instagram_turn_budget_repository.list_records()

    blocked_users = [
        InstagramBlockedUserResponse(
            external_user_id=user_id,
            turn_count=int(record.get("turn_count", 0)),
            blocked=bool(record.get("blocked", False)),
        )
        for user_id, record in blocked_data.items()
    ]

    return InstagramGuardrailsSummaryResponse(
        auto_admit_limit=settings.instagram_auto_admit_limit,
        turn_budget_limit=settings.instagram_turn_budget_limit,
        admitted_count=len(admitted_users),
        blocked_count=len([user for user in blocked_users if user.blocked]),
        admitted_users=admitted_users,
        blocked_users=blocked_users,
    )

@app.get(
    "/internal/instagram/runtime/summary",
    response_model=InstagramRuntimeSummaryResponse,
)
def get_instagram_runtime_summary(
    _: None = Depends(require_internal_api_key),
) -> InstagramRuntimeSummaryResponse:
    pending_outbound_records = instagram_pending_outbound_repository.list_records()
    blocked_records = instagram_turn_budget_repository.list_records()
    now_ts = time.time()

    pending_outbound_count = len(
        [record for record in pending_outbound_records if record.status == "pending"]
    )
    due_pending_outbound = [
        record
        for record in pending_outbound_records
        if record.status == "pending" and record.send_at_ts <= now_ts
    ]
    oldest_pending_outbound = min(
        (
            record
            for record in pending_outbound_records
            if record.status == "pending"
        ),
        key=lambda record: record.send_at_ts,
        default=None,
    )

    oldest_pending_outbound_send_at_ts = (
        oldest_pending_outbound.send_at_ts
        if oldest_pending_outbound is not None
        else None
    )
    oldest_pending_outbound_seconds_until_send = (
        round(oldest_pending_outbound.send_at_ts - now_ts, 2)
        if oldest_pending_outbound is not None
        else None
    )

    blocked_user_count = sum(
        1
        for record in blocked_records.values()
        if bool(record.get("blocked", False))
    )

    return InstagramRuntimeSummaryResponse(
        pending_bundle_count=len(_instagram_pending_bundles),
        deferred_bundle_count=len(_instagram_deferred_bundles),
        ready_bundle_count=len(_instagram_ready_bundles),
        inflight_bundle_count=len(_instagram_inflight_bundle_keys),
        pending_send_bundle_count=len(_instagram_pending_send_bundle_keys),
        ready_queue_count=len(_instagram_ready_bundle_queue),
        active_generation_count=_instagram_active_generation_count,
        max_concurrent_generations=settings.instagram_max_concurrent_generations,
        pending_outbound_count=pending_outbound_count,
        due_pending_outbound_count=len(due_pending_outbound),
        admitted_user_count=instagram_admission_repository.count(),
        blocked_user_count=blocked_user_count,
        oldest_pending_outbound_send_at_ts=oldest_pending_outbound_send_at_ts,
        oldest_pending_outbound_seconds_until_send=oldest_pending_outbound_seconds_until_send,
    )

@app.get(
    "/internal/instagram/runtime/conversations",
    response_model=InstagramRuntimeConversationListResponse,
)
def get_instagram_runtime_conversations(
    _: None = Depends(require_internal_api_key),
) -> InstagramRuntimeConversationListResponse:
    mapping_repository = ConversationMappingRepository()
    chat_repository = LocalChatRepository(settings.chat_history_path)

    mappings = [
        mapping
        for mapping in mapping_repository.load_mappings()
        if mapping.platform == "instagram"
    ]
    turns = chat_repository.load_turns()
    pending_outbound_records = instagram_pending_outbound_repository.list_records()
    admitted_user_ids = set(instagram_admission_repository.list_user_ids())
    blocked_records = instagram_turn_budget_repository.list_records()

    turns_by_session_id: dict[str, list] = {}
    for turn in turns:
        turns_by_session_id.setdefault(turn.session_id, []).append(turn)

    pending_outbound_by_bundle_key: dict[str, list[PendingOutboundMessage]] = {}
    for record in pending_outbound_records:
        if record.status != "pending":
            continue
        pending_outbound_by_bundle_key.setdefault(record.bundle_key, []).append(record)

    mapping_by_bundle_key: dict[str, object] = {}
    all_bundle_keys: set[str] = set()

    for mapping in mappings:
        bundle_key = _build_instagram_bundle_key(
            mapping.external_conversation_id,
            mapping.external_user_id,
        )
        mapping_by_bundle_key[bundle_key] = mapping
        all_bundle_keys.add(bundle_key)

    for bundle_key in _instagram_pending_bundles.keys():
        all_bundle_keys.add(bundle_key)

    for bundle_key in _instagram_deferred_bundles.keys():
        all_bundle_keys.add(bundle_key)

    for bundle_key in _instagram_ready_bundles.keys():
        all_bundle_keys.add(bundle_key)

    for bundle_key in _instagram_inflight_bundle_keys:
        all_bundle_keys.add(bundle_key)

    for bundle_key in _instagram_pending_send_bundle_keys:
        all_bundle_keys.add(bundle_key)

    for bundle_key in pending_outbound_by_bundle_key.keys():
        all_bundle_keys.add(bundle_key)

    conversations: list[InstagramRuntimeConversationResponse] = []

    for bundle_key in sorted(all_bundle_keys):
        mapping = mapping_by_bundle_key.get(bundle_key)

        if mapping is not None:
            external_user_id = mapping.external_user_id
            external_conversation_id = mapping.external_conversation_id
            internal_session_id = mapping.internal_session_id
        else:
            _, external_conversation_id, external_user_id = bundle_key.split(":", 2)
            internal_session_id = None

        session_turns = (
            turns_by_session_id.get(internal_session_id, [])
            if internal_session_id is not None
            else []
        )
        last_turn = session_turns[-1] if session_turns else None

        pending_bundle = _instagram_pending_bundles.get(bundle_key)
        deferred_bundle = _instagram_deferred_bundles.get(bundle_key)
        pending_outbound_for_bundle = pending_outbound_by_bundle_key.get(bundle_key, [])

        conversations.append(
            InstagramRuntimeConversationResponse(
                bundle_key=bundle_key,
                external_user_id=external_user_id,
                external_conversation_id=external_conversation_id,
                internal_session_id=internal_session_id,
                current_runtime_state=_get_instagram_runtime_state(bundle_key),
                last_user_message=(
                    last_turn.user_message.content if last_turn is not None else None
                ),
                last_assistant_message=(
                    last_turn.assistant_message.content if last_turn is not None else None
                ),
                turn_count=len(session_turns),
                admitted=external_user_id in admitted_user_ids,
                blocked=bool(blocked_records.get(external_user_id, {}).get("blocked", False)),
                has_pending_outbound=bool(pending_outbound_for_bundle),
                pending_outbound_count=len(pending_outbound_for_bundle),
                pending_bundle_message_count=(
                    len(pending_bundle.events) if pending_bundle is not None else 0
                ),
                deferred_bundle_message_count=(
                    len(deferred_bundle.events) if deferred_bundle is not None else 0
                ),
            )
        )

    state_priority = {
        "pending_send": 0,
        "inflight": 1,
        "ready": 2,
        "deferred": 3,
        "pending_bundle": 4,
        "idle": 5,
    }

    conversations.sort(
        key=lambda item: (
            state_priority.get(item.current_runtime_state, 99),
            item.external_user_id,
        )
    )

    return InstagramRuntimeConversationListResponse(
        count=len(conversations),
        conversations=conversations,
    )

@app.get(
    "/internal/instagram/runtime/conversations/{external_user_id}",
    response_model=InstagramRuntimeConversationDetailResponse,
)
def get_instagram_runtime_conversation_detail(
    external_user_id: str,
    _: None = Depends(require_internal_api_key),
) -> InstagramRuntimeConversationDetailResponse:
    mapping_repository = ConversationMappingRepository()
    chat_repository = LocalChatRepository(settings.chat_history_path)
    trace_repository = ExternalTraceRepository(settings.external_traces_path)

    mappings = [
        mapping
        for mapping in mapping_repository.load_mappings()
        if mapping.platform == "instagram" and mapping.external_user_id == external_user_id
    ]

    if not mappings:
        raise HTTPException(status_code=404, detail="Instagram conversation not found")

    mapping = mappings[-1]
    bundle_key = _build_instagram_bundle_key(
        mapping.external_conversation_id,
        mapping.external_user_id,
    )

    pending_bundle = _instagram_pending_bundles.get(bundle_key)
    deferred_bundle = _instagram_deferred_bundles.get(bundle_key)

    pending_outbound_records = [
        record
        for record in instagram_pending_outbound_repository.list_records()
        if record.bundle_key == bundle_key and record.status == "pending"
    ]

    all_turns = chat_repository.load_turns()
    session_turns = [
        turn
        for turn in all_turns
        if turn.session_id == mapping.internal_session_id
    ]

    all_traces = trace_repository.load_records()
    conversation_traces = [
        trace
        for trace in all_traces
        if trace.platform == "instagram"
        and trace.external_user_id == external_user_id
        and trace.external_conversation_id == mapping.external_conversation_id
    ]

    now_ts = time.time()

    pending_outbound = [
        InstagramRuntimePendingOutboundResponse(
            pending_id=record.pending_id,
            message_text=record.outbound_message.message_text,
            created_at_ts=record.created_at_ts,
            send_at_ts=record.send_at_ts,
            seconds_until_send=round(record.send_at_ts - now_ts, 2),
            status=record.status,
        )
        for record in sorted(
            pending_outbound_records,
            key=lambda record: record.send_at_ts,
        )
    ]

    recent_turns = [
        InstagramRuntimeTurnResponse(
            user_message=turn.user_message.content,
            assistant_message=turn.assistant_message.content,
        )
        for turn in session_turns[-10:]
    ]

    recent_traces = [
        InstagramRuntimeTraceResponse(
            incoming_message_text=trace.incoming_message_text,
            outgoing_message_text=trace.outgoing_message_text,
            inbound_status=trace.inbound_status,
            outbound_status=trace.outbound_status,
            operational_status=trace.operational_status,
            detail=trace.detail,
            provider_message_id=trace.provider_message_id,
        )
        for trace in conversation_traces[-10:]
    ]

    blocked_records = instagram_turn_budget_repository.list_records()

    return InstagramRuntimeConversationDetailResponse(
        bundle_key=bundle_key,
        external_user_id=mapping.external_user_id,
        external_conversation_id=mapping.external_conversation_id,
        internal_session_id=mapping.internal_session_id,
        current_runtime_state=_get_instagram_runtime_state(bundle_key),
        admitted=instagram_admission_repository.contains(external_user_id),
        blocked=bool(blocked_records.get(external_user_id, {}).get("blocked", False)),
        turn_count=len(session_turns),
        pending_bundle_message_count=(
            len(pending_bundle.events) if pending_bundle is not None else 0
        ),
        deferred_bundle_message_count=(
            len(deferred_bundle.events) if deferred_bundle is not None else 0
        ),
        has_pending_outbound=bool(pending_outbound_records),
        pending_outbound_count=len(pending_outbound_records),
        pending_outbound=pending_outbound,
        recent_turns=recent_turns,
        recent_traces=recent_traces,
    )

@app.get(
    "/internal/instagram/runtime/pending-outbound",
    response_model=InstagramPendingOutboundListResponse,
)
def get_instagram_pending_outbound_runtime(
    _: None = Depends(require_internal_api_key),
) -> InstagramPendingOutboundListResponse:
    mapping_repository = ConversationMappingRepository()
    pending_outbound_records = instagram_pending_outbound_repository.list_records()

    instagram_mappings = [
        mapping
        for mapping in mapping_repository.load_mappings()
        if mapping.platform == "instagram"
    ]

    mapping_by_pair = {
        (mapping.external_conversation_id, mapping.external_user_id): mapping
        for mapping in instagram_mappings
    }

    now_ts = time.time()

    pending_records = [
        record
        for record in pending_outbound_records
        if record.status == "pending"
    ]

    sorted_pending_records = sorted(
        pending_records,
        key=lambda record: record.send_at_ts,
    )

    response_records: list[InstagramPendingOutboundRecordResponse] = []

    for record in sorted_pending_records:
        mapping = mapping_by_pair.get((record.conversation_id, record.user_id))

        response_records.append(
            InstagramPendingOutboundRecordResponse(
                pending_id=record.pending_id,
                bundle_key=record.bundle_key,
                external_user_id=record.user_id,
                external_conversation_id=record.conversation_id,
                internal_session_id=(
                    mapping.internal_session_id if mapping is not None else None
                ),
                message_text=record.outbound_message.message_text,
                status=record.status,
                created_at_ts=record.created_at_ts,
                send_at_ts=record.send_at_ts,
                seconds_until_send=round(record.send_at_ts - now_ts, 2),
            )
        )

    due_count = sum(
        1
        for record in pending_records
        if record.send_at_ts <= now_ts
    )

    oldest_send_at_ts = (
        sorted_pending_records[0].send_at_ts
        if sorted_pending_records
        else None
    )

    return InstagramPendingOutboundListResponse(
        count=len(response_records),
        due_count=due_count,
        oldest_send_at_ts=oldest_send_at_ts,
        records=response_records,
    )

### HTML DASHBOARD PARA RUNTIME DE INSTAGRAM
@app.get("/internal/instagram/runtime/dashboard", response_class=HTMLResponse)
def get_instagram_runtime_dashboard() -> HTMLResponse:
    html = """
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Instagram Runtime Dashboard</title>
        <style>
          :root {
            --bg: #f4f1ea;
            --panel: #fffdf8;
            --panel-strong: #fffaf2;
            --text: #1f1a17;
            --muted: #6e6258;
            --line: #e7ddd0;
            --accent: #b35c2e;
            --accent-soft: #f3dfd1;
            --success: #2f7d4f;
            --warning: #9d6b16;
            --danger: #a13c3c;
            --shadow: 0 10px 30px rgba(46, 32, 20, 0.08);
            --radius: 16px;
          }

          * {
            box-sizing: border-box;
          }

          body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: linear-gradient(180deg, #f7f1e8 0%, #f3ede4 100%);
            color: var(--text);
          }

          .page {
            max-width: 1500px;
            margin: 0 auto;
            padding: 24px;
          }

          .topbar {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
          }

          .title-block h1 {
            margin: 0;
            font-size: 28px;
          }

          .title-block p {
            margin: 6px 0 0;
            color: var(--muted);
          }

          .controls {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
          }

          input[type="password"],
          input[type="text"],
          select {
            border: 1px solid var(--line);
            background: var(--panel);
            border-radius: 12px;
            padding: 10px 12px;
            font-size: 14px;
            color: var(--text);
          }

          button {
            border: 0;
            background: var(--accent);
            color: white;
            border-radius: 12px;
            padding: 10px 14px;
            font-size: 14px;
            cursor: pointer;
          }

          button.secondary {
            background: #d9c6b6;
            color: #2a211c;
          }

          .status-line {
            margin-bottom: 16px;
            color: var(--muted);
            font-size: 14px;
          }

          .card {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
          }

          .metric-card {
            padding: 16px;
          }

          .metric-label {
            color: var(--muted);
            font-size: 13px;
            margin-bottom: 8px;
          }

          .metric-value {
            font-size: 28px;
            font-weight: bold;
          }

          .summary-shell {
            margin-bottom: 20px;
          }

          .summary-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
          }

          .summary-header h2 {
            margin: 0;
            font-size: 20px;
          }

          .summary-guide-toggle {
            cursor: pointer;
            color: var(--accent);
            font-size: 14px;
            font-weight: bold;
          }

          .summary-guide-content {
            margin-bottom: 16px;
          }

          .summary-guide-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 10px;
          }

          .summary-groups {
            display: grid;
            gap: 14px;
          }

          .summary-group {
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 14px;
            background: var(--panel-strong);
          }

          .summary-group h3 {
            margin: 0 0 12px;
            font-size: 15px;
          }

          .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(165px, 1fr));
            gap: 10px;
          }

          .metric-card.flow {
            border-left: 4px solid #7f9cb2;
          }

          .metric-card.generation {
            border-left: 4px solid #c79d38;
          }

          .metric-card.delivery {
            border-left: 4px solid #b35c2e;
          }

          .metric-card.policy {
            border-left: 4px solid #6f7e57;
          }

          .layout {
            display: grid;
            grid-template-columns: 420px 1fr;
            gap: 20px;
          }

          .panel {
            padding: 16px;
          }

          .panel h2 {
            margin: 0 0 12px;
            font-size: 18px;
          }

          .panel h3 {
            margin: 18px 0 10px;
            font-size: 15px;
          }

          .list-toolbar {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 12px;
          }

          .conversation-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-height: 72vh;
            overflow: auto;
          }

          .conversation-item {
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 12px;
            background: var(--panel-strong);
            cursor: pointer;
          }

          .conversation-item.active {
            border-color: var(--accent);
            background: #fff2e8;
          }

          .conversation-top {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            margin-bottom: 8px;
          }

          .conversation-user {
            font-weight: bold;
            font-size: 14px;
          }

          .conversation-preview {
            font-size: 13px;
            color: var(--muted);
            line-height: 1.4;
          }

          .badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 8px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: bold;
            background: #eee3d7;
            color: #533c2c;
          }

          .badge.pending_send {
            background: #fde4d7;
            color: var(--danger);
          }

          .badge.inflight {
            background: #fcefc8;
            color: var(--warning);
          }

          .badge.ready {
            background: #e8efe1;
            color: var(--success);
          }

          .badge.deferred,
          .badge.pending_bundle,
          .badge.idle {
            background: #ece5dc;
            color: #6a5b4d;
          }

          .detail-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
          }

          .detail-box {
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 12px;
            background: var(--panel-strong);
          }

          .detail-kv {
            display: grid;
            grid-template-columns: 180px 1fr;
            gap: 8px;
            font-size: 14px;
            margin-bottom: 8px;
          }

          .detail-kv .key {
            color: var(--muted);
          }

          .stack {
            display: flex;
            flex-direction: column;
            gap: 10px;
          }

          .message-card,
          .trace-card,
          .pending-card {
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 12px;
            background: #fffdf9;
          }

          .message-role,
          .trace-title,
          .pending-title {
            font-size: 12px;
            color: var(--muted);
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
          }

          .empty {
            color: var(--muted);
            font-style: italic;
          }

          .pending-outbound-global {
            margin-top: 20px;
          }

          .pending-global-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 12px;
          }

          @media (max-width: 1100px) {
            .layout {
              grid-template-columns: 1fr;
            }

            .conversation-list {
              max-height: none;
            }

            .detail-grid {
              grid-template-columns: 1fr;
            }
          }
        </style>
      </head>
      <body>
        <div class="page">
          <div class="topbar">
            <div class="title-block">
              <h1>Instagram Runtime Dashboard</h1>
              <p>Internal observability for runtime state, conversations and delayed outbound.</p>
            </div>

            <div class="controls">
              <input id="api-key" type="password" placeholder="Internal API key" />
              <button id="save-key">Save key</button>
              <button id="refresh-btn">Refresh</button>
              <label>
                <input id="auto-refresh" type="checkbox" />
                Auto refresh
              </label>
            </div>
          </div>

          <div id="status-line" class="status-line">Waiting for API key...</div>

          <section class="card panel summary-shell">
            <div class="summary-header">
              <h2>Runtime Summary</h2>
              <div id="summary-guide-toggle" class="summary-guide-toggle">
                Metric Guide · <span id="summary-guide-indicator">Closed</span>
              </div>
            </div>

            <div id="summary-guide-content" class="summary-guide-content" style="display: none;">
              <div class="summary-guide-grid">
                <div class="detail-box">
                  <strong>Flujo entrante</strong>
                  <div><strong>Pending bundles</strong>: mensajes aún dentro de la ventana de bundling.</div>
                  <div><strong>Deferred bundles</strong>: trabajo parado porque esa conversación sigue ocupada.</div>
                  <div><strong>Ready bundles</strong>: bundles ya elegibles para generar.</div>
                  <div><strong>Ready queue</strong>: fila global de bundles listos esperando turno.</div>
                </div>
                <div class="detail-box">
                  <strong>Generación</strong>
                  <div><strong>In-flight</strong>: conversaciones que están generando ahora mismo.</div>
                  <div><strong>Active generations</strong>: cuántas generaciones globales están corriendo ahora.</div>
                  <div><strong>Max generations</strong>: límite global permitido para generación simultánea.</div>
                </div>
                <div class="detail-box">
                  <strong>Entrega</strong>
                  <div><strong>Pending send</strong>: conversaciones con una respuesta ya generada pero aún no enviada.</div>
                  <div><strong>Pending outbound</strong>: mensajes concretos congelados esperando su hora de envío.</div>
                  <div><strong>Due outbound</strong>: mensajes cuyo `send_at` ya venció y deberían salir ya.</div>
                </div>
                <div class="detail-box">
                  <strong>Política</strong>
                  <div><strong>Admitted users</strong>: usuarios autorizados actualmente a entrar en el sistema.</div>
                  <div><strong>Blocked users</strong>: usuarios bloqueados por la policy de turn budget.</div>
                </div>
              </div>
            </div>

            <div class="summary-groups">
              <div class="summary-group">
                <h3>1. Entrada y preparación</h3>
                <div id="summary-flow-grid" class="metric-grid"></div>
              </div>
              <div class="summary-group">
                <h3>2. Generación</h3>
                <div id="summary-generation-grid" class="metric-grid"></div>
              </div>
              <div class="summary-group">
                <h3>3. Entrega diferida</h3>
                <div id="summary-delivery-grid" class="metric-grid"></div>
              </div>
              <div class="summary-group">
                <h3>4. Control de acceso</h3>
                <div id="summary-policy-grid" class="metric-grid"></div>
              </div>
            </div>
          </section>

          <section class="card panel" style="margin-bottom: 20px;">
            <h2 style="display:flex; justify-content:space-between; align-items:center; cursor:pointer;" id="state-guide-toggle">
                Runtime State Guide
                <span id="state-guide-indicator">Closed</span>
            </h2>
      <div id="state-guide-content" style="display: none;">
        <div class="stack">
          <div class="detail-box">
            <strong>idle</strong>
            <div>No hay trabajo activo de runtime en este momento. La conversación existe, pero ahora mismo no está agrupando mensajes, generando ni esperando envío.</div>
          </div>
          <div class="detail-box">
            <strong>pending_bundle</strong>
            <div>Los mensajes entrantes siguen dentro de la ventana de bundling y todavía pueden agruparse antes de pasar al siguiente paso.</div>
          </div>
          <div class="detail-box">
            <strong>deferred</strong>
            <div>Esta conversación tiene más trabajo entrante, pero está esperando temporalmente porque la misma conversación sigue ocupada.</div>
          </div>
          <div class="detail-box">
            <strong>ready</strong>
            <div>El bundle ya es elegible para generación y está esperando su turno dentro del flujo global de ready.</div>
          </div>
          <div class="detail-box">
            <strong>inflight</strong>
            <div>La conversación está generando una respuesta en este momento.</div>
          </div>
          <div class="detail-box">
            <strong>pending_send</strong>
            <div>La respuesta ya se ha generado, pero su envío se está retrasando intencionalmente hasta que llegue su momento programado.</div>
          </div>
        </div>
      </div>
            </section>

          <div class="layout">
            <section class="card panel">
              <h2>Conversations</h2>
              <div class="list-toolbar">
                <input id="search-input" type="text" placeholder="Search user id" />
                <select id="state-filter">
                  <option value="all">All states</option>
                  <option value="pending_send">pending_send</option>
                  <option value="inflight">inflight</option>
                  <option value="ready">ready</option>
                  <option value="deferred">deferred</option>
                  <option value="pending_bundle">pending_bundle</option>
                  <option value="idle">idle</option>
                </select>
              </div>
              <div id="conversation-list" class="conversation-list"></div>
            </section>

            <section class="card panel">
              <h2>Conversation Detail</h2>
              <div id="conversation-detail" class="empty">Select a conversation to inspect it.</div>
            </section>
          </div>

          <section class="card panel pending-outbound-global">
            <h2>Pending Outbound</h2>
            <div id="pending-outbound-summary" class="status-line"></div>
            <div id="pending-global-list" class="pending-global-list"></div>
          </section>
        </div>

        <script>
          const state = {
            apiKey: localStorage.getItem("internal_api_key") || "",
            conversations: [],
            selectedUserId: null,
            autoRefreshTimer: null,
          };

          const summaryFlowGrid = document.getElementById("summary-flow-grid");
          const summaryGenerationGrid = document.getElementById("summary-generation-grid");
          const summaryDeliveryGrid = document.getElementById("summary-delivery-grid");
          const summaryPolicyGrid = document.getElementById("summary-policy-grid");
          const conversationList = document.getElementById("conversation-list");
          const conversationDetail = document.getElementById("conversation-detail");
          const pendingGlobalList = document.getElementById("pending-global-list");
          const pendingOutboundSummary = document.getElementById("pending-outbound-summary");
          const statusLine = document.getElementById("status-line");
          const apiKeyInput = document.getElementById("api-key");
          const searchInput = document.getElementById("search-input");
          const stateFilter = document.getElementById("state-filter");
          const autoRefreshCheckbox = document.getElementById("auto-refresh");

          apiKeyInput.value = state.apiKey;

          function setStatus(text) {
            statusLine.textContent = text;
          }

          function renderMetricCards(container, metrics, variantClass) {
            container.innerHTML = metrics.map(([label, value]) => `
              <div class="card metric-card ${variantClass}">
                <div class="metric-label">${label}</div>
                <div class="metric-value">${value}</div>
              </div>
            `).join("");
          }

          function getHeaders() {
            return {
              "X-Internal-API-Key": state.apiKey,
            };
          }

          async function fetchJson(url) {
            const response = await fetch(url, {
              headers: getHeaders(),
            });

            if (!response.ok) {
              const text = await response.text();
              throw new Error(text || `Request failed: ${response.status}`);
            }

            return response.json();
          }

          function renderSummary(summary) {
            const flowMetrics = [
              ["Pending bundles", summary.pending_bundle_count],
              ["Deferred bundles", summary.deferred_bundle_count],
              ["Ready bundles", summary.ready_bundle_count],
              ["Ready queue", summary.ready_queue_count],
            ];

            const generationMetrics = [
              ["In-flight", summary.inflight_bundle_count],
              ["Active generations", summary.active_generation_count],
              ["Max generations", summary.max_concurrent_generations],
            ];

            const deliveryMetrics = [
              ["Pending send", summary.pending_send_bundle_count],
              ["Pending outbound", summary.pending_outbound_count],
              ["Due outbound", summary.due_pending_outbound_count],
            ];

            const policyMetrics = [
              ["Admitted users", summary.admitted_user_count],
              ["Blocked users", summary.blocked_user_count],
            ];

            renderMetricCards(summaryFlowGrid, flowMetrics, "flow");
            renderMetricCards(summaryGenerationGrid, generationMetrics, "generation");
            renderMetricCards(summaryDeliveryGrid, deliveryMetrics, "delivery");
            renderMetricCards(summaryPolicyGrid, policyMetrics, "policy");
          }

          function conversationMatchesFilters(conversation) {
            const searchValue = searchInput.value.trim().toLowerCase();
            const stateValue = stateFilter.value;

            const matchesSearch =
              !searchValue ||
              conversation.external_user_id.toLowerCase().includes(searchValue);

            const matchesState =
              stateValue === "all" ||
              conversation.current_runtime_state === stateValue;

            return matchesSearch && matchesState;
          }

          function renderConversationList() {
            const filtered = state.conversations.filter(conversationMatchesFilters);

            if (!filtered.length) {
              conversationList.innerHTML = `<div class="empty">No conversations match the current filters.</div>`;
              return;
            }

            conversationList.innerHTML = filtered.map((conversation) => `
                 <div
                    class="conversation-item ${conversation.current_runtime_state} ${state.selectedUserId === conversation.external_user_id ? "active" : ""}"
                    data-user-id="${conversation.external_user_id}"
                    >
                <div class="conversation-top">
                  <div class="conversation-user">${conversation.external_user_id}</div>
                  <span class="badge ${conversation.current_runtime_state}">
                    ${conversation.current_runtime_state}
                  </span>
                </div>
                <div class="conversation-preview">
                  <div><strong>Turns:</strong> ${conversation.turn_count}</div>
                  <div><strong>Pending outbound:</strong> ${conversation.pending_outbound_count}</div>
                  <div><strong>Last user:</strong> ${conversation.last_user_message || "-"}</div>
                </div>
              </div>
            `).join("");

            document.querySelectorAll(".conversation-item").forEach((element) => {
              element.addEventListener("click", () => {
                state.selectedUserId = element.dataset.userId;
                renderConversationList();
                loadConversationDetail();
              });
            });
          }

          function renderPendingOutboundGlobal(data) {
            pendingOutboundSummary.textContent =
              `Count: ${data.count} | Due: ${data.due_count}` +
              (data.oldest_send_at_ts ? ` | Oldest send_at_ts: ${data.oldest_send_at_ts}` : "");

            if (!data.records.length) {
              pendingGlobalList.innerHTML = `<div class="empty">No pending outbound messages.</div>`;
              return;
            }

            pendingGlobalList.innerHTML = data.records.map((record) => `
              <div class="pending-card">
                <div class="pending-title">${record.external_user_id}</div>
                <div><strong>Message:</strong> ${record.message_text}</div>
                <div><strong>State:</strong> ${record.status}</div>
                <div><strong>Seconds until send:</strong> ${record.seconds_until_send}</div>
              </div>
            `).join("");
          }

          function renderConversationDetail(data) {
            const pendingOutboundHtml = data.pending_outbound.length
              ? data.pending_outbound.map((record) => `
                  <div class="pending-card">
                    <div class="pending-title">${record.pending_id}</div>
                    <div><strong>Message:</strong> ${record.message_text}</div>
                    <div><strong>Status:</strong> ${record.status}</div>
                    <div><strong>Seconds until send:</strong> ${record.seconds_until_send}</div>
                  </div>
                `).join("")
              : `<div class="empty">No pending outbound for this conversation.</div>`;

            const turnsHtml = data.recent_turns.length
              ? data.recent_turns.map((turn) => `
                  <div class="message-card">
                    <div class="message-role">User</div>
                    <div>${turn.user_message}</div>
                    <div class="message-role" style="margin-top:10px;">Assistant</div>
                    <div>${turn.assistant_message}</div>
                  </div>
                `).join("")
              : `<div class="empty">No turns available.</div>`;

            const tracesHtml = data.recent_traces.length
              ? data.recent_traces.map((trace) => `
                  <div class="trace-card">
                    <div class="trace-title">${trace.inbound_status} / ${trace.outbound_status || "-"}</div>
                    <div><strong>Incoming:</strong> ${trace.incoming_message_text || "-"}</div>
                    <div><strong>Outgoing:</strong> ${trace.outgoing_message_text || "-"}</div>
                    <div><strong>Operational:</strong> ${trace.operational_status || "-"}</div>
                    <div><strong>Detail:</strong> ${trace.detail}</div>
                  </div>
                `).join("")
              : `<div class="empty">No traces available.</div>`;

            conversationDetail.innerHTML = `
              <div class="detail-grid">
                <div class="detail-box">
                  <h3>Runtime State</h3>
                  <div class="detail-kv"><div class="key">User</div><div>${data.external_user_id}</div></div>
                  <div class="detail-kv"><div class="key">Conversation</div><div>${data.external_conversation_id}</div></div>
                  <div class="detail-kv"><div class="key">Session</div><div>${data.internal_session_id || "-"}</div></div>
                  <div class="detail-kv"><div class="key">State</div><div>${data.current_runtime_state}</div></div>
                  <div class="detail-kv"><div class="key">Turns</div><div>${data.turn_count}</div></div>
                  <div class="detail-kv"><div class="key">Admitted</div><div>${data.admitted}</div></div>
                  <div class="detail-kv"><div class="key">Blocked</div><div>${data.blocked}</div></div>
                  <div class="detail-kv"><div class="key">Pending bundle msgs</div><div>${data.pending_bundle_message_count}</div></div>
                  <div class="detail-kv"><div class="key">Deferred bundle msgs</div><div>${data.deferred_bundle_message_count}</div></div>
                </div>

                <div class="detail-box">
                  <h3>Pending Outbound</h3>
                  <div class="stack">${pendingOutboundHtml}</div>
                </div>
              </div>

              <div class="detail-box" style="margin-top: 12px;">
                <h3>Recent Turns</h3>
                <div class="stack">${turnsHtml}</div>
              </div>

              <div class="detail-box" style="margin-top: 12px;">
                <h3>Recent Traces</h3>
                <div class="stack">${tracesHtml}</div>
              </div>
            `;
          }

          async function loadConversationDetail() {
            if (!state.selectedUserId) {
              conversationDetail.innerHTML = `<div class="empty">Select a conversation to inspect it.</div>`;
              return;
            }

            try {
              const data = await fetchJson(
                `/internal/instagram/runtime/conversations/${state.selectedUserId}`
              );
              renderConversationDetail(data);
            } catch (error) {
              conversationDetail.innerHTML = `<div class="empty">Failed to load detail: ${error.message}</div>`;
            }
          }

          async function refreshDashboard() {
            setStatus("Refreshing dashboard...");

            try {
              const [summary, conversations, pendingOutbound] = await Promise.all([
                fetchJson("/internal/instagram/runtime/summary"),
                fetchJson("/internal/instagram/runtime/conversations"),
                fetchJson("/internal/instagram/runtime/pending-outbound"),
              ]);

              state.conversations = conversations.conversations;

              if (
                state.selectedUserId &&
                !state.conversations.some(
                  (conversation) => conversation.external_user_id === state.selectedUserId
                )
              ) {
                state.selectedUserId = null;
              }

              renderSummary(summary);
              renderConversationList();
              renderPendingOutboundGlobal(pendingOutbound);

              await loadConversationDetail();
              setStatus(`Last refresh: ${new Date().toLocaleTimeString()}`);
            } catch (error) {
              setStatus(`Refresh failed: ${error.message}`);
            }
          }

          function setAutoRefresh(enabled) {
            if (state.autoRefreshTimer) {
              clearInterval(state.autoRefreshTimer);
              state.autoRefreshTimer = null;
            }

            if (enabled) {
              state.autoRefreshTimer = setInterval(refreshDashboard, 5000);
            }
          }

          document.getElementById("save-key").addEventListener("click", () => {
            state.apiKey = apiKeyInput.value.trim();
            localStorage.setItem("internal_api_key", state.apiKey);
            refreshDashboard();
          });

          document.getElementById("refresh-btn").addEventListener("click", refreshDashboard);
          searchInput.addEventListener("input", renderConversationList);
          stateFilter.addEventListener("change", renderConversationList);

          autoRefreshCheckbox.addEventListener("change", (event) => {
            setAutoRefresh(event.target.checked);
          });

          if (state.apiKey) {
            refreshDashboard();
          }

        const stateGuideToggle = document.getElementById("state-guide-toggle");
        const stateGuideContent = document.getElementById("state-guide-content");
        const stateGuideIndicator = document.getElementById("state-guide-indicator");
        const summaryGuideToggle = document.getElementById("summary-guide-toggle");
        const summaryGuideContent = document.getElementById("summary-guide-content");
        const summaryGuideIndicator = document.getElementById("summary-guide-indicator");

        let stateGuideOpen = false;
        let summaryGuideOpen = false;

        stateGuideToggle.addEventListener("click", () => {
        stateGuideOpen = !stateGuideOpen;
        stateGuideContent.style.display = stateGuideOpen ? "block" : "none";
        stateGuideIndicator.textContent = stateGuideOpen ? "Open" : "Closed";
        });

        summaryGuideToggle.addEventListener("click", () => {
        summaryGuideOpen = !summaryGuideOpen;
        summaryGuideContent.style.display = summaryGuideOpen ? "block" : "none";
        summaryGuideIndicator.textContent = summaryGuideOpen ? "Open" : "Closed";
        });

        </script>
      </body>
    </html>
    """
    return HTMLResponse(content=html)



@app.post("/internal/instagram/admission/{external_user_id}", response_model=InstagramGuardrailActionResponse)
def add_instagram_admitted_user(
    external_user_id: str,
    _: None = Depends(require_internal_api_key),
) -> InstagramGuardrailActionResponse:
    added = instagram_admission_repository.add_user_id(external_user_id)

    return InstagramGuardrailActionResponse(
        external_user_id=external_user_id,
        success=True,
        detail="User admitted." if added else "User was already admitted.",
    )

@app.delete("/internal/instagram/admission/{external_user_id}", response_model=InstagramGuardrailActionResponse)
def remove_instagram_admitted_user(
    external_user_id: str,
    _: None = Depends(require_internal_api_key),
) -> InstagramGuardrailActionResponse:
    removed = instagram_admission_repository.remove_user_id(external_user_id)

    return InstagramGuardrailActionResponse(
        external_user_id=external_user_id,
        success=removed,
        detail="User removed from admission list." if removed else "User was not in admission list.",
    )




@app.delete("/internal/instagram/blocklist/{external_user_id}", response_model=InstagramGuardrailActionResponse)
def reset_instagram_blocked_user(
    external_user_id: str,
    _: None = Depends(require_internal_api_key),
) -> InstagramGuardrailActionResponse:
    reset = instagram_turn_budget_repository.reset_user(external_user_id)

    return InstagramGuardrailActionResponse(
        external_user_id=external_user_id,
        success=reset,
        detail="User turn budget was reset." if reset else "User not found in turn budget store.",
    )

@app.delete("/internal/instagram/reset/{external_user_id}", response_model=InstagramUserResetResponse)
def reset_instagram_user_state(
    external_user_id: str,
    _: None = Depends(require_internal_api_key),
) -> InstagramUserResetResponse:
    platform = "instagram"

    memory_repository = build_user_memory_repository(settings)
    memory_deleted = memory_repository.delete_by_user(
        platform=platform,
        external_user_id=external_user_id,
    )

    admission_removed = instagram_admission_repository.remove_user_id(external_user_id)
    turn_budget_reset = instagram_turn_budget_repository.reset_user(external_user_id)

    mapping_repository = ConversationMappingRepository()
    mappings = mapping_repository.list_by_user(platform=platform, external_user_id=external_user_id)
    session_ids = [mapping.internal_session_id for mapping in mappings]

    chat_repository = LocalChatRepository(settings.chat_history_path)
    chat_turns_deleted = chat_repository.delete_turns_by_session_ids(session_ids)

    mappings_deleted = mapping_repository.delete_by_user(
        platform=platform,
        external_user_id=external_user_id,
    )

    return InstagramUserResetResponse(
        external_user_id=external_user_id,
        memory_deleted=memory_deleted,
        admission_removed=admission_removed,
        turn_budget_reset=turn_budget_reset,
        mappings_deleted=mappings_deleted,
        chat_turns_deleted=chat_turns_deleted,
        detail="Instagram user state reset completed.",
    )




##################################################################


######################## WEBHOOKS ####################################
@app.post("/webhooks/messages")
def receive_webhook_message(request: WebhookMessageRequest) -> MessageResponse | WebhookEventResponse:
    
    inbound_service = build_platform_inbound_service(settings)

    payload = PlatformWebhookPayload(
        platform=request.platform,
        event_type=request.event_type,
        conversation_id=request.conversation_id,
        user_id=request.user_id,
        message_text=request.message_text,
        message_id=request.message_id,
        payload_id=request.payload_id,
        raw_payload=request.channel_metadata,
    )

    

    try:
        inbound_result = inbound_service.process_payload(payload)

        if inbound_result.status == "ignored":
            return WebhookEventResponse(
                status="ignored",
                detail=inbound_result.detail
            )
        if inbound_result.channel_result is None:
            return HTTPException(
                status_code=500,
                detail = "Parser returned no event for a processable payload"
            )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {exc}") from exc
    except GenerationProviderError as exc:
        raise HTTPException(status_code=503, detail=f"Generation provider error: {exc}") from exc

    turn = inbound_result.channel_result.turn

    return MessageResponse(
        session_id=turn.session_id,
        user_message=turn.user_message.content,
        assistant_message=turn.assistant_message.content
    )



###################### INSTAGRAM RECIBE MENSAJE EN DM #######################################

@app.post("/providers/instagram/webhook/messages", response_model=WebhookEventResponse)
async def receive_instagram_webhook_message(request: Request) -> WebhookEventResponse:
    raw_body = await request.body()
    signature_header = request.headers.get("X-Hub-Signature-256")

    _validate_instagram_webhook_signature(raw_body, signature_header)

    raw_payload = _decode_instagram_webhook_payload(raw_body)
    provider_payload_request = _parse_instagram_webhook_request(raw_body)
    provider_payload = InstagramWebhookPayload.from_dict(
        provider_payload_request.model_dump(mode="json")
    )

    _store_instagram_raw_payload(raw_payload)
    provider_parser_result, external_events = _build_external_events(provider_payload)
    trace_repository = ExternalTraceRepository(settings.external_traces_path)


    if not external_events:
        _save_ignored_instagram_provider_event_trace(
            trace_repository=trace_repository,
            provider_parser_result=provider_parser_result,
        )
        return WebhookEventResponse(
            status="ignored",
            detail=provider_parser_result.detail,
        )

    if external_events:
        external_event = external_events[0]

        if trace_repository.has_processed_provider_message(external_event.message_id):
            return WebhookEventResponse(
                status="ignored",
                detail="Duplicate provider message ignored.",
            )
        
        if not settings.bot_enabled:
            _save_bot_disabled_trace(trace_repository, external_event)
            return WebhookEventResponse(
                status="accepted",
                detail="Instagram message captured, but bot is disabled. No response was sent.",
            )
        
        if not _is_instagram_user_allowed(external_event.user_id):
            _save_user_not_allowed_trace(trace_repository, external_event)
            return WebhookEventResponse(status="accepted", detail="Instagram message captured, but user is not allowed. No response was sent.")


        if _is_instagram_user_blocked(external_event.user_id):
            _save_turn_budget_blocked_trace(trace_repository, external_event)
            return WebhookEventResponse(
                status="accepted",
                detail="Instagram message captured, but user is blocked by turn budget policy. No response was sent.",
            )

        if _is_instagram_user_rate_limited(external_event.user_id):
            _save_rate_limited_trace(trace_repository, external_event)
            return WebhookEventResponse(
                status="accepted",
                detail = "Instagram message captured, but user is rate limited. No response was sent"
            )


        if external_event.message_id and external_event.message_id in _instagram_buffered_message_ids:
            return WebhookEventResponse(
                status="ignored",
                detail="Duplicate buffered provider message ignored.",
            )

        enqueue_status = _enqueue_instagram_event(external_event)

        if enqueue_status == "duplicate_buffered":
            return WebhookEventResponse(
                status="ignored",
                detail="Duplicate buffered provider message ignored.",
            )

        return WebhookEventResponse(
            status="accepted",
            detail="Instagram message buffered for bundling.",
        )




    response_status = "accepted" if provider_parser_result.status == "captured" else "ignored"
    return WebhookEventResponse(
        status=response_status,
        detail=provider_parser_result.detail,
    )

### VERIFICACION INSTAGRAM ###
@app.get("/providers/instagram/webhook/messages")
def verify_instagram_webhook_messages(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
):
    return execute_webhook_verification(
        mode=hub_mode,
        token=hub_token,
        challenge=hub_challenge,
    )


@app.get("/webhooks/verify")
def verify_generic_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
):
    return execute_webhook_verification(mode=hub_mode, token=hub_token, challenge=hub_challenge)


#==============FUNCIONES_AUXILIARES=====================



def execute_webhook_verification(mode: str, token: str, challenge: str):
    if mode != "subscribe":
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    if token != settings.webhook_verify_token:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    # IMPORTANTE: Retornamos Response para enviar texto plano, no JSON
    return Response(content=challenge, media_type="text/plain")


def _parse_instagram_webhook_request(raw_body: bytes) -> InstagramWebhookPayloadRequest:
    try:
        return InstagramWebhookPayloadRequest.model_validate_json(raw_body)
    except ValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid Instagram webhook payload",
        ) from exc


def _decode_instagram_webhook_payload(raw_body: bytes) -> dict:
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=400,
            detail="Instagram webhook payload is not valid JSON",
        ) from exc

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=400,
            detail="Instagram webhook payload must be a JSON object",
        )

    return payload


def _store_instagram_raw_payload(raw_payload: dict) -> None:
    raw_payload_repository = ProviderRawPayloadRepository(settings.provider_raw_payloads_path)
    raw_payload_repository.save_record(
        ProviderRawPayloadRecord(
            provider="instagram",
            endpoint="/providers/instagram/webhook/messages",
            payload=raw_payload,
        )
    )


def _build_external_events(
    provider_payload: InstagramWebhookPayload,
) -> tuple[ProviderPayloadParseResult, list[ExternalMessageEvent]]:
    parser = InstagramPayloadParser()
    provider_parser_result = parser.parse(provider_payload)

    external_events: list[ExternalMessageEvent] = []
    for parsed_event in provider_parser_result.events:
        external_event = parsed_event.to_external_message_event()
        if external_event is not None:
            external_events.append(external_event)

    return provider_parser_result, external_events


def _get_instagram_bundle_key(external_event: ExternalMessageEvent) -> str:
    return f"{external_event.platform}:{external_event.conversation_id}:{external_event.user_id}"


def _merge_instagram_bundles(
    target_bundle: PendingInstagramBundle,
    incoming_bundle: PendingInstagramBundle,
) -> PendingInstagramBundle:
    target_bundle.events.extend(incoming_bundle.events)
    return target_bundle


def _defer_instagram_bundle(bundle: PendingInstagramBundle) -> None:
    existing_bundle = _instagram_deferred_bundles.get(bundle.bundle_key)

    if existing_bundle is None:
        _instagram_deferred_bundles[bundle.bundle_key] = bundle
        return

    _merge_instagram_bundles(existing_bundle, bundle)


def _is_instagram_bundle_inflight(bundle_key: str) -> bool:
    return bundle_key in _instagram_inflight_bundle_keys


def _mark_instagram_bundle_inflight(bundle_key: str) -> None:
    _instagram_inflight_bundle_keys.add(bundle_key)


def _clear_instagram_bundle_inflight(bundle_key: str) -> None:
    _instagram_inflight_bundle_keys.discard(bundle_key)

def _is_instagram_bundle_pending_send(bundle_key: str) -> bool:
    return bundle_key in _instagram_pending_send_bundle_keys


def _mark_instagram_bundle_pending_send(bundle_key: str) -> None:
    _instagram_pending_send_bundle_keys.add(bundle_key)


def _clear_instagram_bundle_pending_send(bundle_key: str) -> None:
    _instagram_pending_send_bundle_keys.discard(bundle_key)


def _is_instagram_bundle_busy(bundle_key: str) -> bool:
    return _is_instagram_bundle_inflight(bundle_key) or _is_instagram_bundle_pending_send(bundle_key)

def _get_instagram_runtime_state(bundle_key: str) -> str:
    if bundle_key in _instagram_pending_send_bundle_keys:
        return "pending_send"

    if bundle_key in _instagram_inflight_bundle_keys:
        return "inflight"

    if bundle_key in _instagram_ready_bundles:
        return "ready"

    if bundle_key in _instagram_deferred_bundles:
        return "deferred"

    if bundle_key in _instagram_pending_bundles:
        return "pending_bundle"

    return "idle"

def _build_instagram_bundle_key(
    conversation_id: str,
    external_user_id: str,
) -> str:
    return f"instagram:{conversation_id}:{external_user_id}"



def _is_instagram_bundle_ready(bundle_key: str) -> bool:
    return bundle_key in _instagram_ready_bundles


def _enqueue_ready_instagram_bundle(bundle: PendingInstagramBundle) -> None:
    existing_bundle = _instagram_ready_bundles.get(bundle.bundle_key)

    if existing_bundle is None:
        _instagram_ready_bundles[bundle.bundle_key] = bundle
    else:
        _merge_instagram_bundles(existing_bundle, bundle)

    if bundle.bundle_key not in _instagram_ready_bundle_keys:
        _instagram_ready_bundle_queue.append(bundle.bundle_key)
        _instagram_ready_bundle_keys.add(bundle.bundle_key)


def _schedule_instagram_generation_dispatch() -> None:
    global _instagram_generation_dispatch_task

    if (
        _instagram_generation_dispatch_task is not None
        and not _instagram_generation_dispatch_task.done()
    ):
        return

    loop = asyncio.get_running_loop()
    _instagram_generation_dispatch_task = loop.create_task(
        _dispatch_instagram_ready_bundles()
    )


def _on_instagram_generation_task_done(task: asyncio.Task) -> None:
    global _instagram_active_generation_count

    _instagram_active_generation_count = max(0, _instagram_active_generation_count - 1)

    try:
        task.result()
    except Exception:
        pass

    _schedule_instagram_generation_dispatch()


async def _dispatch_instagram_ready_bundles() -> None:
    global _instagram_generation_dispatch_task
    global _instagram_active_generation_count

    try:
        max_concurrent_generations = max(1, settings.instagram_max_concurrent_generations)

        while (
            _instagram_active_generation_count < max_concurrent_generations
            and _instagram_ready_bundle_queue
        ):
            bundle_key = _instagram_ready_bundle_queue.popleft()
            _instagram_ready_bundle_keys.discard(bundle_key)

            if _is_instagram_bundle_busy(bundle_key):
                blocked_bundle = _instagram_ready_bundles.pop(bundle_key, None)
                if blocked_bundle is not None and blocked_bundle.events:
                    _defer_instagram_bundle(blocked_bundle)
                continue

            bundle = _instagram_ready_bundles.pop(bundle_key, None)
            if bundle is None or not bundle.events:
                continue

            _instagram_active_generation_count += 1

            generation_task = asyncio.create_task(
                _process_instagram_ready_bundle(bundle)
            )
            generation_task.add_done_callback(_on_instagram_generation_task_done)
    finally:
        _instagram_generation_dispatch_task = None



def _schedule_instagram_bundle_flush(
    bundle_key: str,
    delay_seconds: float | None = None,
) -> bool:
    if bundle_key in _instagram_bundle_tasks:
        return False

    loop = asyncio.get_running_loop()
    _instagram_bundle_tasks[bundle_key] = loop.create_task(
        _flush_instagram_bundle_after_delay(bundle_key, delay_seconds)
    )
    return True


def _requeue_deferred_instagram_bundle(bundle_key: str) -> bool:
    deferred_bundle = _instagram_deferred_bundles.pop(bundle_key, None)
    if deferred_bundle is None or not deferred_bundle.events:
        return False

    pending_bundle = _instagram_pending_bundles.get(bundle_key)
    if pending_bundle is None:
        _instagram_pending_bundles[bundle_key] = deferred_bundle
    else:
        _merge_instagram_bundles(pending_bundle, deferred_bundle)

    _schedule_instagram_bundle_flush(bundle_key, delay_seconds=0)
    return True

def _build_instagram_outbound_send_delay_seconds() -> int:
    min_delay = settings.instagram_outbound_delay_min_seconds
    max_delay = settings.instagram_outbound_delay_max_seconds

    if max_delay < min_delay:
        max_delay = min_delay

    return random.randint(min_delay, max_delay)


def _build_pending_outbound_message(
    bundle_key: str,
    bundle: PendingInstagramBundle,
    channel_result: HttpChannelResult,
    preferred_language: str,
) -> PendingOutboundMessage:
    delay_seconds = _build_instagram_outbound_send_delay_seconds()
    now_ts = time.time()

    return PendingOutboundMessage(
        pending_id=str(uuid.uuid4()),
        bundle_key=bundle_key,
        platform=bundle.platform,
        conversation_id=bundle.conversation_id,
        user_id=bundle.user_id,
        turn=channel_result.turn,
        outbound_message=channel_result.outbound_message,
        original_events=list(bundle.events),
        preferred_language=preferred_language,
        created_at_ts=now_ts,
        send_at_ts=now_ts + delay_seconds,
        status="pending",
        last_error=None,
    )


async def _send_pending_outbound_record(record: PendingOutboundMessage) -> None:
    trace_repository = ExternalTraceRepository(settings.external_traces_path)
    instagram_sender = InstagramOutboundSender(settings)

    send_result = await asyncio.to_thread(
        instagram_sender.send,
        record.outbound_message,
    )

    channel_result = HttpChannelResult(
        turn=record.turn,
        outbound_message=record.outbound_message,
    )

    for original_event in record.original_events:
        _save_processed_trace(
            trace_repository=trace_repository,
            external_event=original_event,
            channel_result=channel_result,
            send_result=send_result,
        )

    if send_result.status == "sent":
        _remember_instagram_reply(record.user_id)
        _increment_instagram_turn_budget(record.user_id)

    instagram_pending_outbound_repository.remove_record(record.pending_id)
    _clear_instagram_bundle_pending_send(record.bundle_key)

    for original_event in record.original_events:
        if original_event.message_id:
            _instagram_buffered_message_ids.discard(original_event.message_id)

    _requeue_deferred_instagram_bundle(record.bundle_key)


async def _process_due_pending_outbounds() -> None:
    now_ts = time.time()
    due_records = instagram_pending_outbound_repository.list_due_records(now_ts)

    for record in due_records:
        await _send_pending_outbound_record(record)


async def _instagram_outbound_scheduler_loop() -> None:
    while True:
        try:
            await _process_due_pending_outbounds()
        except Exception:
            pass

        await asyncio.sleep(settings.instagram_outbound_scheduler_poll_seconds)


async def _process_instagram_ready_bundle(bundle: PendingInstagramBundle) -> None:
    bundle_key = bundle.bundle_key
    marked_inflight = False

    try:
        if _is_instagram_bundle_busy(bundle_key):
            _defer_instagram_bundle(bundle)
            return

        _mark_instagram_bundle_inflight(bundle_key)
        marked_inflight = True

        combined_event = _build_combined_instagram_event(bundle)
        trace_repository = ExternalTraceRepository(settings.external_traces_path)

        force_final_turn_budget_message = _should_send_turn_budget_final_message(bundle.user_id)

        bundle_preferred_language = detect_conversation_language(
            current_message=combined_event.message_text,
            recent_user_messages=[event.message_text for event in bundle.events[:-1]],
        )

        try:
            channel_result = await asyncio.to_thread(
                _build_channel_result_for_external_event,
                combined_event,
            )

            if force_final_turn_budget_message:
                channel_result.outbound_message.message_text = _build_instagram_turn_budget_final_message(
                    bundle_preferred_language
                )

            pending_outbound = _build_pending_outbound_message(
                bundle_key=bundle_key,
                bundle=bundle,
                channel_result=channel_result,
                preferred_language=bundle_preferred_language,
            )
            instagram_pending_outbound_repository.add_record(pending_outbound)
            _mark_instagram_bundle_pending_send(bundle_key)

        except GenerationProviderError as exc:
            for original_event in bundle.events:
                _save_failed_processing_trace(trace_repository, original_event, str(exc))
            return
        except Exception as exc:
            for original_event in bundle.events:
                _save_failed_processing_trace(
                    trace_repository,
                    original_event,
                    f"Unexpected bundled processing error: {exc}",
                )
            return

    finally:
        if marked_inflight:
            _clear_instagram_bundle_inflight(bundle_key)

            if not _is_instagram_bundle_pending_send(bundle_key):
                for event in bundle.events:
                    if event.message_id:
                        _instagram_buffered_message_ids.discard(event.message_id)

                _requeue_deferred_instagram_bundle(bundle_key)


def _enqueue_instagram_event(external_event: ExternalMessageEvent) -> str:
    bundle_key = _get_instagram_bundle_key(external_event)

    if external_event.message_id and external_event.message_id in _instagram_buffered_message_ids:

        return "duplicate_buffered"
    
    bundle = _instagram_pending_bundles.get(bundle_key)
    if bundle is None: 
        bundle = PendingInstagramBundle(
            bundle_key=bundle_key,
            platform=external_event.platform,
            conversation_id=external_event.conversation_id,
            user_id=external_event.user_id
        )
        _instagram_pending_bundles[bundle_key] = bundle

    bundle.events.append(external_event)

    if external_event.message_id:
        _instagram_buffered_message_ids.add(external_event.message_id)

    if bundle_key not in _instagram_bundle_tasks:
        _schedule_instagram_bundle_flush(bundle_key)
        return "queued_new_bundle"
    
    return "queued_existing_bundle"


def _build_combined_instagram_event(bundle: PendingInstagramBundle) -> ExternalMessageEvent:
    combined_text = "\n".join(
        event.message_text.strip()
        for event in bundle.events
        if event.message_text and event.message_text.strip()
    )

    last_event = bundle.events[-1]
    bundled_message_ids = [
        event.message_id
        for event in bundle.events
        if event.message_id
    ]

    return ExternalMessageEvent(
        platform=bundle.platform,
        conversation_id=bundle.conversation_id,
        user_id=bundle.user_id,
        message_text=combined_text,
        message_id=last_event.message_id,
        channel_metadata={
            "source": "instagram_bundle",
            "bundled_count": len(bundle.events),
            "bundled_message_ids": bundled_message_ids,
        },
    )


async def _flush_instagram_bundle_after_delay(bundle_key: str, delay_seconds: float | None = None) -> None:
    bundle: PendingInstagramBundle | None = None

    try: 
        effective_delay = (
            settings.instagram_bundle_window_seconds
            if delay_seconds is None else delay_seconds
        )

        if effective_delay > 0:
            await asyncio.sleep(effective_delay)

        bundle = _instagram_pending_bundles.pop(bundle_key, None)
        if bundle is None or not bundle.events:
            return
        
        if _is_instagram_bundle_busy(bundle_key):
            _defer_instagram_bundle(bundle)
            return 

        _enqueue_ready_instagram_bundle(bundle)
        _schedule_instagram_generation_dispatch()


    finally:
        _instagram_bundle_tasks.pop(bundle_key, None)



def _build_instagram_turn_budget_final_message(preferred_language: str) -> str:
    redirect_url = settings.instagram_redirect_url.strip() or "https://example.com/private"
    if settings.instagram_behavior_profile.strip().lower() != "redirecting_dm":
        if preferred_language == "en":
            return (
                "i am going to pause here for now, but thanks for the conversation"
            )

        return "voy a dejarlo aqui por ahora, pero gracias por la conversacion"

    if preferred_language == "en":
        return (
            f"if you want to keep talking to me, talk to me here {redirect_url}, "
            "my instagram is too crowded and i am not really using it for this"
        )

    return (
        f"si quieres que sigamos hablando hablame por aqui {redirect_url}, "
        "que el instagram lo tengo petado y no lo uso mucho para esto"
    )


def _should_send_turn_budget_final_message(external_user_id: str) -> bool:
    limit = settings.instagram_turn_budget_limit

    if limit <= 0:
        return False

    current_turn_count = instagram_turn_budget_repository.get_turn_count(external_user_id)
    next_turn_count = current_turn_count + 1

    return next_turn_count >= limit

def _build_channel_result_for_external_event(external_event: ExternalMessageEvent) -> HttpChannelResult:
    channel_adapter = build_http_channel_adapter(settings)
    return channel_adapter.process_event(external_event)



def _process_and_send_external_event(external_event: ExternalMessageEvent) -> tuple[HttpChannelResult, OutboundSendResult]:
    channel_adapter = build_http_channel_adapter(settings)
    channel_result = channel_adapter.process_event(external_event)

    instagram_sender = InstagramOutboundSender(settings)

    try:
        send_result = instagram_sender.send(channel_result.outbound_message)
    except Exception as exc:
        send_result = OutboundSendResult(
            status = "failed",
            detail = f"Instagram outbound sender raised an unexpected error: {exc}",
            external_message_id = None,
        )

    return channel_result, send_result


def _save_processed_trace(
    trace_repository: ExternalTraceRepository,
    external_event: ExternalMessageEvent,
    channel_result: HttpChannelResult,
    send_result: OutboundSendResult,
) -> None:
    
    turn_metadata = channel_result.turn.session_metadata or {}

    outbound_failed = send_result.status != "sent"
    operational_status = "outbound_failed" if outbound_failed else "ok"
    operational_error_type = "instagram_outbound_failed" if outbound_failed else None


    trace_repository.save_records(
        ExternalTraceRecord(
            platform="instagram",
            external_conversation_id=external_event.conversation_id,
            external_user_id=external_event.user_id,
            internal_session_id=channel_result.turn.session_id,
            incoming_message_text=external_event.message_text,
            outgoing_message_text=channel_result.outbound_message.message_text,
            inbound_status="processed",
            outbound_status=send_result.status,
            detail=f"Inbound Instagram message processed by internal core. Outbound result: {send_result.detail}",
            provider_message_id=external_event.message_id,
            outbound_message_id=send_result.external_message_id,
            operational_status=operational_status,
            operational_error_type=operational_error_type,
            operational_detail=send_result.detail,
            memory_loaded=turn_metadata.get("memory_loaded"),
            memory_updated=turn_metadata.get("memory_updated"),
            memory_profile_status=turn_metadata.get("memory_profile_status"),
            memory_profile_detail=turn_metadata.get("memory_profile_detail"),
            memory_profile_matched_rule=turn_metadata.get("memory_profile_matched_rule"),
            memory_summary_status=turn_metadata.get("memory_summary_status"),
            memory_summary_detail=turn_metadata.get("memory_summary_detail"),
            memory_summary_matched_rule=turn_metadata.get("memory_summary_matched_rule"),
            style_preset=turn_metadata.get("style_preset"),
            style_snapshot=turn_metadata.get("style_snapshot"),
            safety_policy_active=turn_metadata.get("safety_policy_active"),
            safety_snapshot=turn_metadata.get("safety_snapshot"),
            safety_validation_status=turn_metadata.get("safety_validation_status"),
            safety_validation_detail=turn_metadata.get("safety_validation_detail"),
            safety_matched_rule=turn_metadata.get("safety_matched_rule"),

        )
    )

def _save_failed_processing_trace(
    trace_repository: ExternalTraceRepository,
    external_event: ExternalMessageEvent,
    detail: str,
) -> None:
    trace_repository.save_records(
        ExternalTraceRecord(
            platform="instagram",
            external_conversation_id=external_event.conversation_id,
            external_user_id=external_event.user_id,
            internal_session_id=None,
            incoming_message_text=external_event.message_text,
            outgoing_message_text=None,
            inbound_status="processing_failed",
            outbound_status="not_sent",
            detail=f"Inbound Instagram message accepted, but processing failed before outbound send: {detail}",
            provider_message_id=external_event.message_id,
            outbound_message_id=None,
            operational_status="processing_failed",
            operational_error_type="generation_provider_error",
            operational_detail=detail,

        )
    )

def _save_bot_disabled_trace(
    trace_repository: ExternalTraceRepository,
    external_event: ExternalMessageEvent,
) -> None:
    trace_repository.save_records(
        ExternalTraceRecord(
            platform="instagram",
            external_conversation_id=external_event.conversation_id,
            external_user_id=external_event.user_id,
            internal_session_id=None,
            incoming_message_text=external_event.message_text,
            outgoing_message_text=None,
            inbound_status="captured",
            outbound_status="not_sent",
            detail="Inbound Instagram message captured, but bot is disabled.",
            provider_message_id=external_event.message_id,
            outbound_message_id=None,
            operational_status="bot_disabled",
            operational_error_type=None,
            operational_detail="BOT_ENABLED=false. Message was captured without generating or sending a response.",
        )
    ) 

def _save_user_not_allowed_trace(
    trace_repository: ExternalTraceRepository,
    external_event: ExternalMessageEvent,
) -> None:
    trace_repository.save_records(
        ExternalTraceRecord(
            platform="instagram",
            external_conversation_id=external_event.conversation_id,
            external_user_id=external_event.user_id,
            internal_session_id=None,
            incoming_message_text=external_event.message_text,
            outgoing_message_text=None,
            inbound_status="captured",
            outbound_status="not_sent",
            detail="Inbound Instagram message captured, but user was not admitted.",
            provider_message_id=external_event.message_id,
            outbound_message_id=None,
            operational_status="user_not_allowed",
            operational_error_type=None,
            operational_detail="User was not admitted by the current Instagram admission policy",
        )
    )


def _save_turn_budget_blocked_trace(
    trace_repository: ExternalTraceRepository,
    external_event: ExternalMessageEvent,
) -> None:
    trace_repository.save_records(
        ExternalTraceRecord(
            platform="instagram",
            external_conversation_id=external_event.conversation_id,
            external_user_id=external_event.user_id,
            internal_session_id=None,
            incoming_message_text=external_event.message_text,
            outgoing_message_text=None,
            inbound_status="captured",
            outbound_status="not_sent",
            detail="Inbound Instagram message captured, but user is blocked by turn budget policy.",
            provider_message_id=external_event.message_id,
            outbound_message_id=None,
            operational_status="turn_budget_blocked",
            operational_error_type=None,
            operational_detail="User exceeded INSTAGRAM_TURN_BUDGET_LIMIT and is currently blocked.",
        )
    )


def _save_rate_limited_trace(
    trace_repository: ExternalTraceRepository,
    external_event: ExternalMessageEvent,
) -> None:
    trace_repository.save_records(
        ExternalTraceRecord(
            platform="instagram",
            external_conversation_id=external_event.conversation_id,
            external_user_id=external_event.user_id,
            internal_session_id=None,
            incoming_message_text=external_event.message_text,
            outgoing_message_text=None,
            inbound_status="captured",
            outbound_status="not_sent",
            detail="Inbound Instagram message captured, but user is rate limited.",
            provider_message_id=external_event.message_id,
            outbound_message_id=None,
            operational_status="rate_limited",
            operational_error_type=None,
            operational_detail="INSTAGRAM_REPLY_COOLDOWN_SECONDS prevented an automatic response.",
        )
    )


def _save_ignored_instagram_provider_event_trace(
        trace_repository: ExternalTraceRepository,
        provider_parser_result: ProviderPayloadParseResult,
) -> None:
    first_event = provider_parser_result.events[0] if provider_parser_result.events else None

    trace_repository.save_records(
        ExternalTraceRecord(
            platform="instagram",
            external_conversation_id=(
                first_event.external_conversation_id if first_event else "unknown"
            ),
            external_user_id=(
                first_event.external_user_id if first_event else "unknown"
            ),
            internal_session_id=None,
            incoming_message_text=(
                first_event.incoming_message_text if first_event else None
            ),
            outgoing_message_text=None,
            inbound_status="ignored",
            outbound_status=None,
            detail=provider_parser_result.detail,
            provider_message_id=(
                first_event.provider_message_id if first_event else None
            ),
            outbound_message_id=None,
            operational_status="unsupported_input",
            operational_error_type=None,
            operational_detail=(
                first_event.detail if first_event else provider_parser_result.detail
            ),
            memory_loaded=None,
            memory_updated=None,
        )
    )



def _validate_instagram_webhook_signature(raw_body: bytes, signature_header: str | None) -> None:
    if not settings.instagram_app_secret:
        raise HTTPException(
            status_code=500,
            detail="INSTAGRAM_APP_SECRET is not configured",
        )

    if not signature_header:
        raise HTTPException(status_code=403, detail="Missing webhook signature")

    expected_signature = "sha256=" + hmac.new(
        settings.instagram_app_secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature_header.strip()):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")
    


###########   MEMORIA  #############
def _to_user_memory_response(memory) -> UserMemoryResponse:
    return UserMemoryResponse(
        platform=memory.platform,
        external_user_id=memory.external_user_id,
        last_known_username=memory.last_known_username,
        user_profile=memory.user_profile,
        conversation_summary=memory.conversation_summary,
        stable_facts=memory.stable_facts,
        preferences=memory.preferences,
        relationship_notes=memory.relationship_notes,
        updated_at=memory.updated_at,
        last_seen_at=memory.last_seen_at,
    )


########### OPERATION ###############3
def _to_operational_event_response(record: ExternalTraceRecord) -> OperationalEventResponse:
    return OperationalEventResponse(
        platform=record.platform,
        external_conversation_id=record.external_conversation_id,
        external_user_id=record.external_user_id,
        internal_session_id=record.internal_session_id,
        incoming_message_text=record.incoming_message_text,
        outgoing_message_text=record.outgoing_message_text,
        inbound_status=record.inbound_status,
        outbound_status=record.outbound_status,
        detail=record.detail,
        provider_message_id=record.provider_message_id,
        outbound_message_id=record.outbound_message_id,
        operational_status=record.operational_status,
        operational_error_type=record.operational_error_type,
        operational_detail=record.operational_detail,
        memory_loaded=record.memory_loaded,
        memory_updated=record.memory_updated,
        style_preset=record.style_preset,
        safety_validation_status=record.safety_validation_status,
    )


###############

def _is_instagram_user_allowed(external_user_id: str) -> bool:
    allowed_user_ids = settings.instagram_allowed_user_ids

    # If a manual allowlist is configured, it has priority.
    if allowed_user_ids:
        return external_user_id in allowed_user_ids

    auto_admit_limit = settings.instagram_auto_admit_limit

    # If the auto-admit limit is disabled or non-positive, allow everyone.
    if auto_admit_limit <= 0:
        return True

    if instagram_admission_repository.contains(external_user_id):
        return True

    if instagram_admission_repository.count() >= auto_admit_limit:
        return False

    instagram_admission_repository.add_user_id(external_user_id)
    return True

def _is_instagram_user_blocked(external_user_id: str) -> bool:
    return instagram_turn_budget_repository.is_blocked(external_user_id)

def _increment_instagram_turn_budget(external_user_id: str) -> dict[str, int | bool]:
    return instagram_turn_budget_repository.increment_turn(
        external_user_id,
        settings.instagram_turn_budget_limit,
    )



def _is_instagram_user_rate_limited(external_user_id: str) -> bool:
    cooldown_seconds = settings.instagram_reply_cooldown_seconds

    if cooldown_seconds <= 0:
        return False
    
    last_reply_at = _instagram_last_reply_by_user.get(external_user_id)

    if last_reply_at is None:
        return False
    
    elapsed_seconds = time.monotonic() - last_reply_at

    return elapsed_seconds < cooldown_seconds

def _remember_instagram_reply(external_user_id: str) -> None:
    if settings.instagram_reply_cooldown_seconds <= 0:
        return
    
    _instagram_last_reply_by_user[external_user_id] = time.monotonic()
