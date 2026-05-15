from pydantic import BaseModel, ConfigDict, Field

class MessageRequest(BaseModel):
    message: str = Field(..., min_length=1, description="El mensaje del usuario")
    session_id: str = Field(..., min_length=1, description="ID de la sesión")

class MessageResponse(BaseModel):
    user_message: str = Field(..., description="El mensaje del usuario")
    assistant_message: str = Field(..., description="La respuesta del asistente")
    session_id: str = Field(..., description="ID de la sesión")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Estado de la API")
    
class InfoResponse(BaseModel):
    service_name: str = Field(..., description="Nombre del servicio")
    version: str = Field(..., description="Versión del servicio")
    enviroment: str = Field(..., description="Entorno de ejecución")
    llm_provider: str = Field(..., description="Proveedor de LLM utilizado")


class WebhookMessageRequest(BaseModel):
    
    platform: str = Field(...,min_length=1, description="Plataforma de origen del mensaje")
    event_type: str = Field(..., min_length=1, description="Tipo de evento externo")
    conversation_id: str = Field(..., min_length=1, description="ID de la conversación")
    user_id: str = Field(..., min_length=1, description="ID del usuario")
    message_text: str = Field(..., min_length=1, description="Texto del mensaje")
    message_id: str | None = Field(default=None, description="ID del mensaje, si está disponible")
    payload_id: str | None = Field(default=None, description="Payload externo")
    channel_metadata: dict | None = Field(default=None, description="Metadatos específicos del canal")


class WebhookVerifyResponse(BaseModel):
    challenge: str = Field(..., description="Desafío para verificar el webhook")


class WebhookEventResponse(BaseModel):
    status: str = Field(..., description="Estado del procesamiento del evento")
    detail: str | None = Field(default=None, description="Detalles adicionales sobre el procesamiento del evento")


class InstagramWebhookUserRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(..., min_length=1, description="Instagram scoped identifier")


class InstagramWebhookMessageRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    mid: str | None = Field(default=None, description="External message identifier")
    text: str | None = Field(default=None, description="Message text")
    is_echo: bool | None = Field(default=None, description="Whether the event is an echo")


class InstagramWebhookMessagingRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    sender: InstagramWebhookUserRequest
    recipient: InstagramWebhookUserRequest
    timestamp: int | None = Field(default=None, description="Message timestamp")
    message: InstagramWebhookMessageRequest | None = Field(default=None, description="Message payload")


class InstagramWebhookChangeValueRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    sender: InstagramWebhookUserRequest | None = Field(default=None, description="External sender identifier")
    recipient: InstagramWebhookUserRequest | None = Field(default=None, description="External recipient identifier")
    timestamp: int | str | None = Field(default=None, description="Message timestamp")
    message: InstagramWebhookMessageRequest | None = Field(default=None, description="Message payload")


class InstagramWebhookChangeRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    field: str = Field(..., min_length=1, description="Webhook field name")
    value: InstagramWebhookChangeValueRequest | None = Field(default=None, description="Webhook change value")


class InstagramWebhookEntryRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(..., min_length=1, description="Provider entry identifier")
    time: int | None = Field(default=None, description="Entry timestamp")
    messaging: list[InstagramWebhookMessagingRequest] = Field(
        default_factory=list,
        description="List of provider messaging events",
    )
    changes: list[InstagramWebhookChangeRequest] = Field(
        default_factory=list,
        description="List of provider change events",
    )


class InstagramWebhookPayloadRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    object: str = Field(..., min_length=1, description="Provider object name")
    entry: list[InstagramWebhookEntryRequest] = Field(
        default_factory=list,
        description="List of provider entry objects",
    )

class InstagramUserResetResponse(BaseModel):
    external_user_id: str
    memory_deleted: bool
    admission_removed: bool
    turn_budget_reset: bool
    mappings_deleted: int
    chat_turns_deleted: int
    detail: str



class UserMemoryResponse(BaseModel):
    platform : str
    external_user_id : str
    last_known_username: str | None = None
    user_profile : str | None = None
    conversation_summary : str | None = None
    stable_facts: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    relationship_notes: list[str] = Field(default_factory=list)
    updated_at: str | None = None
    last_seen_at: str | None = None

class UserMemoryListResponse(BaseModel):
    platform : str
    count : int
    memories : list[UserMemoryResponse]

class UserMemoryDeleteResponse(BaseModel):
    platform : str
    external_user_id : str
    deleted: bool
    detail: str


class UserMemoryCleanupResponse(BaseModel):
    deleted_count: int
    detail: str

class OperationalEventResponse(BaseModel):
    platform: str
    external_conversation_id: str
    external_user_id: str
    internal_session_id: str | None = None
    incoming_message_text: str | None = None
    outgoing_message_text: str | None = None
    inbound_status: str
    outbound_status: str | None = None
    detail: str
    provider_message_id: str | None = None
    outbound_message_id: str | None = None
    operational_status: str | None = None
    operational_error_type: str | None = None
    operational_detail: str | None = None
    memory_loaded: bool | None = None
    memory_updated: bool | None = None
    style_preset: str | None = None
    safety_validation_status: str | None = None


class OperationalEventListResponse(BaseModel):
    count: int
    events: list[OperationalEventResponse]


class OperationalSummaryResponse(BaseModel):
    platform: str | None = None
    total: int
    inbound_status_counts: dict[str, int]
    outbound_status_counts: dict[str, int]
    operational_status_counts: dict[str, int]
    operational_error_type_counts: dict[str, int]


class CharacterSummaryResponse(BaseModel):
    character_id: str
    display_name: str
    file_path: str

class CharacterListResponse(BaseModel):
    count: int
    characters: list[CharacterSummaryResponse]

class ActiveCharacterResponse(BaseModel):
    character_id: str
    display_name: str
    file_path: str | None = None
    is_default: bool
    load_status: str
    load_detail: str | None = None


class InstagramBlockedUserResponse(BaseModel):
    external_user_id: str
    turn_count: int
    blocked: bool


class InstagramGuardrailsSummaryResponse(BaseModel):
    auto_admit_limit: int
    turn_budget_limit: int
    admitted_count: int
    blocked_count: int
    admitted_users: list[str]
    blocked_users: list[InstagramBlockedUserResponse]


class InstagramGuardrailActionResponse(BaseModel):
    external_user_id: str
    success: bool
    detail: str


class InstagramRuntimeSummaryResponse(BaseModel):
    pending_bundle_count: int
    deferred_bundle_count: int
    ready_bundle_count: int
    inflight_bundle_count: int
    pending_send_bundle_count: int
    ready_queue_count: int
    active_generation_count: int
    max_concurrent_generations: int
    pending_outbound_count: int
    due_pending_outbound_count: int
    admitted_user_count: int
    blocked_user_count: int
    oldest_pending_outbound_send_at_ts: float | None = None
    oldest_pending_outbound_seconds_until_send: float | None = None


class InstagramRuntimeConversationResponse(BaseModel):
    bundle_key: str
    external_user_id: str
    external_conversation_id: str
    internal_session_id: str | None = None
    current_runtime_state: str
    last_user_message: str | None = None
    last_assistant_message: str | None = None
    turn_count: int
    admitted: bool
    blocked: bool
    has_pending_outbound: bool
    pending_outbound_count: int
    pending_bundle_message_count: int
    deferred_bundle_message_count: int


class InstagramRuntimeConversationListResponse(BaseModel):
    count: int
    conversations: list[InstagramRuntimeConversationResponse]


class InstagramRuntimePendingOutboundResponse(BaseModel):
    pending_id: str
    message_text: str
    created_at_ts: float
    send_at_ts: float
    seconds_until_send: float
    status: str


class InstagramRuntimeTurnResponse(BaseModel):
    user_message: str
    assistant_message: str


class InstagramRuntimeTraceResponse(BaseModel):
    incoming_message_text: str | None = None
    outgoing_message_text: str | None = None
    inbound_status: str
    outbound_status: str | None = None
    operational_status: str | None = None
    detail: str
    provider_message_id: str | None = None


class InstagramRuntimeConversationDetailResponse(BaseModel):
    bundle_key: str
    external_user_id: str
    external_conversation_id: str
    internal_session_id: str | None = None
    current_runtime_state: str
    admitted: bool
    blocked: bool
    turn_count: int
    pending_bundle_message_count: int
    deferred_bundle_message_count: int
    has_pending_outbound: bool
    pending_outbound_count: int
    pending_outbound: list[InstagramRuntimePendingOutboundResponse]
    recent_turns: list[InstagramRuntimeTurnResponse]
    recent_traces: list[InstagramRuntimeTraceResponse]


class InstagramPendingOutboundRecordResponse(BaseModel):
    pending_id: str
    bundle_key: str
    external_user_id: str
    external_conversation_id: str
    internal_session_id: str | None = None
    message_text: str
    status: str
    created_at_ts: float
    send_at_ts: float
    seconds_until_send: float


class InstagramPendingOutboundListResponse(BaseModel):
    count: int
    due_count: int
    oldest_send_at_ts: float | None = None
    records: list[InstagramPendingOutboundRecordResponse]






    

    


