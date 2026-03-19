from app.models.chat import ChatMessage, ChatTurn
from app.services.conversation_service import ConversationService



class ChatOrchestrator:
    def __init__(self, conversation_service: ConversationService) -> None:
        self.conversation_service = conversation_service

    def handle_message(self, message: ChatMessage, session_id: str) -> ChatTurn:
        turn = self.conversation_service.process_message(message, session_id)
        return turn
    
    def get_session_history(self, session_id: str, limit: int = 3) -> list[ChatTurn]:
        return self.conversation_service.get_session_history(
            session_id, 
            limit
            )