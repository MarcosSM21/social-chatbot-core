from pydantic import BaseModel, Field

class MessageRequest(BaseModel):
    message: str = Field(..., min_length=1, description="El mensaje del usuario")
    session_id: str = Field(..., min_length=1, description="ID de la sesión")

class MessageResponse(BaseModel):
    user_message: str = Field(..., description="El mensaje del usuario")
    assistant_message: str = Field(..., description="La respuesta del asistente")
    session_id: str = Field(..., description="ID de la sesión")