from app.engine.response_engine import ResponseEngine
from app.models.chat import ChatMessage, ChatTurn
from app.storage.local_chat_repository import LocalChatRepository

class ConversationService:
    def __init__(
            self,
            response_engine: ResponseEngine,
            chat_repository: LocalChatRepository
        ) -> None:  
        self.response_engine = response_engine
        self.chat_repository = chat_repository
    
    def process_message(self, message: ChatMessage, session_id: str) -> ChatTurn:
        recent_history = self.chat_repository.get_recent_turns(session_id, limit=3)

        assistant_message = self.response_engine.generate_response(message=message, history=recent_history)

        turn = ChatTurn(
            session_id=session_id,
            user_message=message,
            assistant_message=assistant_message
        )

        self.chat_repository.save_turn(turn)

        return turn 
    
    def get_session_history(self, session_id: str, limit: int = 3) -> list[ChatTurn]:
        return self.chat_repository.get_recent_turns(
            session_id=session_id,
            limit=limit
        )