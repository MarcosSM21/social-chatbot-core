from app.models.chat import ChatMessage, ChatTurn
from app.models.external import ExternalMessageEvent
from app.orchestrator.chat_orquestrator import ChatOrchestrator
from app.storage.conversation_mapping_repository import ConversationMappingRepository
from app.channels.http_channel_result import HttpChannelResult
from app.models.outbound import OutboundChannelMessage

class HttpChannelAdapter:
    """HTTP-based implementation of a channel adapter"""

    def __init__(self, orchestrator: ChatOrchestrator, mapping_repository: ConversationMappingRepository) -> None:
        self.orchestrator = orchestrator
        self.mapping_repository = mapping_repository

    def process_event(self, event: ExternalMessageEvent) -> HttpChannelResult:
        
        internal_session_id = self.mapping_repository.get_or_create_session_id(
            platform=event.platform,
            external_conversation_id=event.conversation_id,
            external_user_id=event.user_id
        )
        
        user_message = ChatMessage(role="user", content=event.message_text)
        turn = self.orchestrator.handle_message(message=user_message, session_id=internal_session_id)

        outbound_message = OutboundChannelMessage(
            platform=event.platform,
            conversation_id=event.conversation_id,
            user_id = event.user_id,
            message_text=turn.assistant_message.content,
            channel_metadata={
                "source": "assistant_reply",
                "reply_to_message_id": event.message_id,
            },
        )


        return HttpChannelResult(
            turn = turn,
            outbound_message=outbound_message
        )