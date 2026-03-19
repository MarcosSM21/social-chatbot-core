from app.engine.response_engine import ResponseEngine
from app.models.chat import ChatMessage, ChatTurn
from app.storage.local_chat_repository import LocalChatRepository

class ChatOrchestrator:
    def __init__(self, response_engine: ResponseEngine, chat_repository: LocalChatRepository) -> None:
        
        self.response_engine = response_engine
        self.chat_repository = chat_repository

    def handle_message(self, message: ChatMessage) -> ChatTurn:
        assistant_message = self.response_engine.generate_response(message)

        turn = ChatTurn(
            user_message=message,
            assistant_message=assistant_message
        )

        self.chat_repository.save_turn(turn)

        return turn