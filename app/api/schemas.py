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


class UserMemoryResponse(BaseModel):
    platform : str
    external_user_id : str
    user_profile : str | None = None
    conversation_summary : str | None = None
    stable_facts: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    relationship_notes: list[str] = Field(default_factory=list)
    updated_at: str | None = None

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


