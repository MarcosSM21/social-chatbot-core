from app.models.chat import ChatMessage, ChatTurn
from app.models.external import ExternalMessageEvent
from app.orchestrator.chat_orquestrator import ChatOrchestrator
from app.storage.conversation_mapping_repository import ConversationMappingRepository

class HttpChannelAdapter:
    """HTTP-based implementation of a channel adapter"""

    def __init__(self, orchestrator: ChatOrchestrator, mapping_repository: ConversationMappingRepository) -> None:
        self.orchestrator = orchestrator
        self.mapping_repository = mapping_repository

    def process_event(self, event: ExternalMessageEvent) -> ChatTurn:
        
        internal_session_id = self.mapping_repository.get_or_create_session_id(
            platform=event.platform,
            external_conversation_id=event.conversation_id,
            external_user_id=event.user_id
        )
        
        user_message = ChatMessage(role="user", content=event.message_text)
        turn = self.orchestrator.handle_message(message=user_message, session_id=internal_session_id)
        return turn 