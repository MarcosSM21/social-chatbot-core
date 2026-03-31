from datetime import datetime, UTC

from app.engine.response_engine import ResponseEngine
from app.models.chat import ChatMessage, ChatTurn
from app.storage.local_chat_repository import LocalChatRepository
from app.services.conversation_context_builder import ConversationContextBuilder
from app.storage.user_memory_repository import UserMemoryRepository


class ConversationService:
    def __init__(
        self,
        response_engine: ResponseEngine,
        chat_repository: LocalChatRepository,
        context_builder: ConversationContextBuilder,
        user_memory_repository: UserMemoryRepository,
    ) -> None:
        self.response_engine = response_engine
        self.chat_repository = chat_repository
        self.context_builder = context_builder
        self.user_memory_repository = user_memory_repository

    def process_message(
        self,
        message: ChatMessage,
        session_id: str,
        platform: str,
        external_user_id: str,
    ) -> ChatTurn:
        recent_history = self.chat_repository.get_recent_turns(session_id, limit=3)

        existing_memory = self.user_memory_repository.get_or_create(
            platform=platform,
            external_user_id=external_user_id,
        )

        memory_loaded = bool(
            existing_memory.user_profile or existing_memory.conversation_summary
        )

        context = self.context_builder.build(
            platform=platform,
            external_user_id=external_user_id,
            message=message,
            recent_history=recent_history,
        )

        assistant_message = self.response_engine.generate_response(context=context)

        self._update_user_memory(
            platform=platform,
            external_user_id=external_user_id,
            user_message=message,
            assistant_message=assistant_message,
        )

        turn = ChatTurn(
            session_id=session_id,
            user_message=message,
            assistant_message=assistant_message,
            session_metadata={
                "memory_loaded": memory_loaded,
                "memory_updated": True,
            },
        )

        self.chat_repository.save_turn(turn)

        return turn 
    
    def get_session_history(self, session_id: str, limit: int = 3) -> list[ChatTurn]:
        return self.chat_repository.get_recent_turns(
            session_id=session_id,
            limit=limit,
        )
    
    def _update_user_memory(
        self,
        platform: str,
        external_user_id: str,
        user_message: ChatMessage,
        assistant_message: ChatMessage,
    ) -> None:
        memory = self.user_memory_repository.get_or_create(
            platform=platform,
            external_user_id=external_user_id,
        )

        memory.user_profile = self._build_user_profile(
            current_profile=memory.user_profile,
            user_message=user_message.content,
        )

        memory.conversation_summary = self._build_conversation_summary(
            current_summary=memory.conversation_summary,
            user_message=user_message.content,
            assistant_message=assistant_message.content,
        )

        memory.updated_at = datetime.now(UTC).isoformat()

        self.user_memory_repository.save(memory)


    def _build_user_profile(self, current_profile: str | None, user_message: str) -> str | None:
        text = user_message.strip()
        lowered = text.lower()

        candidate_fact = None

        if lowered.startswith("me llamo "):
            candidate_fact = text
        elif lowered.startswith("mi nombre es "):
            candidate_fact = text
        elif lowered.startswith("prefiero "):
            candidate_fact = text
        elif lowered.startswith("me gusta "):
            candidate_fact = text
        elif lowered.startswith("no me gusta "):
            candidate_fact = text

        if not candidate_fact:
            return current_profile
        
        if not current_profile:
            return candidate_fact
        
        if candidate_fact.lower() in current_profile.lower():
            return current_profile
        
        return f"{current_profile}\n{candidate_fact}"
    


    def _build_conversation_summary(self, current_summary: str | None, user_message: str, assistant_message: str) -> str:
        latest_exchange = (
            f"User said: {user_message.strip()} "
            f"Assistant replied: {assistant_message.strip()}"
        )

        if not current_summary:
            return latest_exchange[:600]
        
        combined = f"{current_summary}\n{latest_exchange}"
        return combined[-600:]
