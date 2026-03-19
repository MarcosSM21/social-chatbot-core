from fastapi import FastAPI

from app.api.schemas import MessageRequest, MessageResponse

app = FastAPI(
    title="social-chatbot-core API",
    version="0.1.0",
    description="Interanl API para el chatbot social core project"
)

@app.get("/")
def root() -> dict:
    return {
        "message": "social-chatbot-core API is running",
        "status": "ok"
    }


@app.post("/messages", response_model=MessageResponse)
def create_message(request: MessageRequest) -> MessageResponse:
    return MessageResponse(
        user_message=request.message,
        assistant_message=(f"Mock Echo: {request.message}"),      
        session_id=request.session_id
    )