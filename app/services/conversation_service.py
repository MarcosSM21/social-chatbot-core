from datetime import datetime, UTC
import re

from app.engine.response_engine import ResponseEngine
from app.models.chat import ChatMessage, ChatTurn
from app.storage.local_chat_repository import LocalChatRepository
from app.services.conversation_context_builder import ConversationContextBuilder
from app.storage.user_memory_repository import UserMemoryRepository
from app.services.assistant_response_safety_validator import AssistantResponseSafetyValidator
from app.services.user_memory_safety_validator import UserMemorySafetyValidator
from app.models.user_memory import UserMemory
from app.services.memory_summarizer import MemorySummarizer, RuleBasedMemorySummarizer




class ConversationService:
    def __init__(
        self,
        response_engine: ResponseEngine,
        chat_repository: LocalChatRepository,
        context_builder: ConversationContextBuilder,
        user_memory_repository: UserMemoryRepository,
        response_safety_validator: AssistantResponseSafetyValidator,
        memory_safety_validator: UserMemorySafetyValidator,
        memory_summarizer: MemorySummarizer | None = None,
    ) -> None:
        self.response_engine = response_engine
        self.chat_repository = chat_repository
        self.context_builder = context_builder
        self.user_memory_repository = user_memory_repository
        self.response_safety_validator = response_safety_validator
        self.memory_safety_validator = memory_safety_validator
        self.memory_summarizer = memory_summarizer or RuleBasedMemorySummarizer()

    def process_message(
        self,
        message: ChatMessage,
        session_id: str,
        platform: str,
        external_user_id: str,
    ) -> ChatTurn:
        recent_history = self.chat_repository.get_recent_turns(session_id, limit=3)

        existing_memory = self.user_memory_repository.get_by_user(
            platform=platform,
            external_user_id=external_user_id,
        )

        memory_loaded = self._has_meaningful_memory(existing_memory)

        context = self.context_builder.build(
            platform=platform,
            external_user_id=external_user_id,
            message=message,
            recent_history=recent_history,
        )

        assistant_message = self.response_engine.generate_response(context=context)
        safety_validation = self.response_safety_validator.validate(assistant_message.content)

        assistant_message = ChatMessage(
            role="assistant",
            content = safety_validation.safe_text
        )

        memory_update_metadata = self._update_user_memory(
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
                "memory_updated": memory_update_metadata["memory_updated"],
                "memory_profile_status": memory_update_metadata["memory_profile_status"],
                "memory_profile_detail": memory_update_metadata["memory_profile_detail"],
                "memory_profile_matched_rule": memory_update_metadata["memory_profile_matched_rule"],
                "memory_summary_status": memory_update_metadata["memory_summary_status"],
                "memory_summary_detail": memory_update_metadata["memory_summary_detail"],
                "memory_summary_matched_rule": memory_update_metadata["memory_summary_matched_rule"],
                "character_id": context.character.character_id,
                "character_name": context.character.display_name,
                "character_snapshot": context.character.to_dict(),
                "safety_policy_active": True,
                "safety_snapshot": context.safety_policy.to_dict(),
                "safety_validation_status": safety_validation.status,
                "safety_validation_detail": safety_validation.detail,
                "safety_matched_rule": safety_validation.matched_rule,
            },
        )

        self.chat_repository.save_turn(turn)

        return turn 
    
    def get_session_history(self, session_id: str, limit: int = 3) -> list[ChatTurn]:
        return self.chat_repository.get_recent_turns(
            session_id=session_id,
            limit=limit,
        )
    
    def _has_meaningful_memory(self, memory: UserMemory | None) -> bool:
        if memory is None:
            return False


        return bool(
            memory.user_profile
            or memory.conversation_summary
            or memory.stable_facts
            or memory.preferences
            or memory.relationship_notes
        )
    
    def _update_user_memory(
        self,
        platform: str,
        external_user_id: str,
        user_message: ChatMessage,
        assistant_message: ChatMessage,
    ) -> dict:
        memory = self.user_memory_repository.get_by_user(
            platform=platform,
            external_user_id=external_user_id,
        ) or UserMemory(
            platform=platform,
            external_user_id=external_user_id,
        )

        original_profile = memory.user_profile
        original_summary = memory.conversation_summary
        original_stable_facts = list(memory.stable_facts)
        original_preferences = list(memory.preferences)
        original_relationship_notes = list(memory.relationship_notes)


        candidate_profile_fact = self._extract_user_profile_candidate(
            user_message=user_message.content,
        )
        profile_safety = self.memory_safety_validator.validate_candidate_memory(
            candidate_profile_fact,
        )

        if candidate_profile_fact and profile_safety.status == "passed":
            memory.user_profile = self._merge_user_profile(
                current_profile=memory.user_profile,
                candidate_fact=candidate_profile_fact,
            )     

            memory_type, memory_value = self._classify_profile_candidate(candidate_profile_fact)

            if memory_type == "stable_fact" and memory_value:
                memory.stable_facts = self._append_unique_memory_item(items=memory.stable_facts, candidate=memory_value)   

            if memory_type == "preference" and memory_value:
                memory.preferences = self._append_unique_memory_item(items=memory.preferences, candidate=memory_value)


        candidate_summary = self.memory_summarizer.summarize(
            current_summary=memory.conversation_summary,
            user_message=user_message.content,
            assistant_message=assistant_message.content,
        )

        summary_safety = self.memory_safety_validator.validate_candidate_memory(
            candidate_summary,
        )

        if summary_safety.status == "passed":
            memory.conversation_summary = candidate_summary

        memory_updated = (
            memory.user_profile != original_profile
            or memory.conversation_summary != original_summary
            or memory.stable_facts != original_stable_facts
            or memory.preferences != original_preferences
            or memory.relationship_notes != original_relationship_notes
        )


        if memory_updated:
            memory.updated_at = datetime.now(UTC).isoformat()
            self.user_memory_repository.save(memory)

        return {
            "memory_updated": memory_updated,
            "memory_profile_status": profile_safety.status,
            "memory_profile_detail": profile_safety.detail,
            "memory_profile_matched_rule": profile_safety.matched_rule,
            "memory_summary_status": summary_safety.status,
            "memory_summary_detail": summary_safety.detail,
            "memory_summary_matched_rule": summary_safety.matched_rule,
        }


    def _extract_user_profile_candidate(self, user_message: str) -> str | None:
        text = user_message.strip()

        name_candidate = self._extract_name_candidate(text)
        if name_candidate:
            return name_candidate

        preference_candidate = self._extract_preference_candidate(text)
        if preference_candidate:
            return preference_candidate

        return None

    def _extract_name_candidate(self, text: str) -> str | None:
        me_llamo_match = re.search(r"\bme llamo\s+([^,.!?]+)", text, re.IGNORECASE)
        if me_llamo_match:
            name = me_llamo_match.group(1).strip()
            return f"me llamo {name}"

        mi_nombre_match = re.search(r"\bmi nombre es\s+([^,.!?]+)", text, re.IGNORECASE)
        if mi_nombre_match:
            name = mi_nombre_match.group(1).strip()
            return f"mi nombre es {name}"

        return None

    def _extract_preference_candidate(self, text: str) -> str | None:
        preference_patterns = [
            ("no me gusta", r"^\s*no me gusta\s+([^,.!?]+)"),
            ("me gusta", r"^\s*me gusta\s+([^,.!?]+)"),
            ("prefiero", r"\bprefiero\s+([^,.!?]+)"),
        ]

        for prefix, pattern in preference_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                preference = match.group(1).strip()
                return f"{prefix} {preference}"

        return None


    
    def _merge_user_profile(
        self,
        current_profile: str | None,
        candidate_fact: str,
    ) -> str:
        if not current_profile:
            return candidate_fact

        if candidate_fact.lower() in current_profile.lower():
            return current_profile

        return f"{current_profile}\n{candidate_fact}"

    def _append_unique_memory_item(self, items: list[str], candidate: str) -> list[str]:
        normalized_candidate = candidate.strip().lower()

        if not normalized_candidate:
            return items
        
        for item in items: 
            if item.strip().lower() == normalized_candidate:
                return items
            
        return [*items, candidate.strip()]
    
    def _classify_profile_candidate(self, candidate_fact: str | None) -> tuple[str | None, str | None]:
        if not candidate_fact:
            return None, None
        
        lowered = candidate_fact.lower()

        if lowered.startswith("me llamo") or lowered.startswith("mi nombre es "):
            return "stable_fact", candidate_fact
        
        if (
            lowered.startswith("prefiero ")
            or lowered.startswith("me gusta ")
            or lowered.startswith("no me gusta ")
        ):
            return "preference", candidate_fact

        return None, None
    
