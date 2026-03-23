from pydantic import BaseModel, Field

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

