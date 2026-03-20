from app.models.chat import ChatMessage, ChatTurn
from app.models.external import ExternalMessageEvent
from app.orchestrator.chat_orquestrator import ChatOrchestrator

class HttpChannelAdapter:
    """HTTP-based implementation of a channel adapter"""

    def __init__(self, orchestrator: ChatOrchestrator) -> None:
        self.orchestrator = orchestrator

    def process_event(self, event: ExternalMessageEvent) -> ChatTurn:
        user_message = ChatMessage(role="user", content=event.message_text)
        turn = self.orchestrator.handle_message(message=user_message, session_id=event.conversation_id)
        return turn