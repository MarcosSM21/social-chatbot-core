from app.models.chat import ChatMessage, ChatTurn
from app.services.conversation_service import ConversationService



class ChatOrchestrator:
    def __init__(self, conversation_service: ConversationService) -> None:
        self.conversation_service = conversation_service

    def handle_message(self, message: ChatMessage, session_id: str) -> ChatTurn:
        turn = self.conversation_service.process_message(message, session_id)
        return turn
    
