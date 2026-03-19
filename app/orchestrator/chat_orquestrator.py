from app.engine.response_engine import ResponseEngine
from app.models.chat import ChatMessage, ChatTurn

class ChatOrchestrator:
    def __init__(self, response_engine: ResponseEngine) -> None:
        self.response_engine = response_engine

    def handle_message(self, message: ChatMessage) -> ChatTurn:
        assistant_message = self.response_engine.generate_response(message)

        return ChatTurn(user_message=message, assistant_message=assistant_message)