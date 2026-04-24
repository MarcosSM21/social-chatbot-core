from app.core.settings import Settings
from app.models.chat import ChatMessage, ChatTurn
from app.models.conversation_safety import ConversationSafetyPolicy
from app.models.conversation_context import ConversationContext
from app.storage.user_memory_repository import UserMemoryRepository
from app.models.conversation_character import ConversationCharacter
from app.storage.character_repository import CharacterRepository
from app.models.user_memory import UserMemory




class ConversationContextBuilder:
    def __init__(self, settings: Settings, user_memory_repository: UserMemoryRepository, character_repository: CharacterRepository | None = None) -> None:
        self.settings = settings
        self.user_memory_repository = user_memory_repository
        self.character_repository = character_repository or CharacterRepository()

    def build(self, platform: str, external_user_id : str, message: ChatMessage, recent_history: list[ChatTurn] ) -> ConversationContext:

        user_memory = self.user_memory_repository.get_by_user(
            platform=platform,
            external_user_id=external_user_id
        ) or UserMemory (
            platform=platform,
            external_user_id=external_user_id,
        )

        retrieved_memory = self._select_relevant_memory(
            user_memory=user_memory,
            current_message=message.content,
        )

        safety_policy = self._build_safety_policy()
        character = self._build_character()

        return ConversationContext(
            current_message=message,
            recent_history=recent_history,
            system_instructions=self._build_system_instructions(),
            safety_policy=safety_policy,
            safety_instructions=self._build_safety_instructions(safety_policy),
            character=character,
            character_instructions=self._build_character_instructions(character),
            user_profile=user_memory.user_profile,
            conversation_summary=user_memory.conversation_summary,            
            stable_facts=user_memory.stable_facts,
            preferences=user_memory.preferences,
            relationship_notes=user_memory.relationship_notes,
            retrieved_memory=retrieved_memory,
            retrieval_strategy="rule_based_memory_selector_v1"
        )

    def _build_system_instructions(self) -> str:
        return (
            "You are replying in a private chat. "
            "Your conversational identity, voice, and boundaries come from the active character instructions. "
            "Use memory and recent conversation only when relevant"
        )
    
    def _build_safety_policy(self) -> ConversationSafetyPolicy:
        return ConversationSafetyPolicy.default()
    
    def _build_safety_instructions(self, safety_policy: ConversationSafetyPolicy) -> str:
        rules_text = " ".join(safety_policy.risk_rules)

        return (
            "Safety rules: "
            f"Protect secrets: {safety_policy.protect_secrets}. "
            f"Protect internal instructions: {safety_policy.protect_internal_instructions}. "
            f"Prevent cross-user leaks: {safety_policy.prevent_cross_user_leaks}. "
            f"Prevent false memory claims: {safety_policy.prevent_false_memory_claims}. "
            f"Avoid sensitive memory storage: {safety_policy.avoid_sensitive_memory_storage}. "
            f"{rules_text}"
        )
    
    def _build_character(self) -> ConversationCharacter:
        return self.character_repository.load_by_file_path(self.settings.character_file)

    def _build_character_instructions(self, character: ConversationCharacter) -> str:
        return "\n".join(
        [
            "Active character brief.",
            f"Name: {character.display_name}.",
            "Use this character as the only conversational identity.",
            "",
            "Identity:",
            character.core_identity,
            "",
            "Inner world:",
            self._compact_text(character.inner_world, max_chars=450),
            "",
            "Backstory:",
            self._compact_text(character.backstory, max_chars=450),
            "",
            "Personality:",
            self._compact_list(character.personality_traits, limit=8),
            "",
            "Motivations:",
            self._compact_list(character.motivations, limit=5),
            "",
            "Relationship dynamic:",
            character.relationship_to_user,
            self._compact_list(character.relationship_dynamic, limit=5),
            "",
            "Voice:",
            self._compact_list(character.speaking_style, limit=8),
            self._compact_list(character.voice_guidelines, limit=8),
            "",
            "Conversation habits:",
            self._compact_list(character.conversation_habits, limit=6),
            "",
            "Response principles:",
            self._compact_list(character.response_principles, limit=8),
            "",
            "Boundaries:",
            self._compact_list(character.boundaries, limit=8),
            "",
            "Avoid:",
            self._compact_list(character.avoid_phrases, limit=8),
            self._compact_list(character.do_not_perform, limit=8),
            "",
            "Important:",
            "Do not copy fixed example phrases.",
            "Do not mention the character profile.",
            "Do not explain your own personality.",
            "Answer the user's actual message.",
        ]
    )


    def _compact_text(self, text: str, max_chars: int) -> str:
        normalized = " ".join(text.split())

        if len(normalized) <= max_chars:
            return normalized
        
        return normalized[: max_chars - 3].rstrip() + "..."
    
    def _compact_list(self, items: list[str], limit:int) -> str:
        selected_items = [item.strip() for item in items[:limit] if item.strip()]

        if not selected_items: 
            return "- none"
        
        return "\n".join(f"- {item}" for item in selected_items)


    def _select_relevant_memory(
        self,
        user_memory: UserMemory,
        current_message: str,
    ) -> list[str]:
        message_lower = current_message.strip().lower()
        selected: list[str] = []

        identity_cues = ("nombre", "llamo", "name", "remember", "recuerd")
        preference_cues = ("prefiero", "prefer", "gusta", "like", "respuesta", "respond", "tono")
        relationship_cues = ("trato", "hablas", "tono", "broma", "vacil", "sobreexpl")

        if user_memory.user_profile and (
            self._contains_any(message_lower, identity_cues)
            or self._has_keyword_overlap(message_lower, user_memory.user_profile)
        ):
            selected.append(f"Profile: {user_memory.user_profile}")

        for fact in user_memory.stable_facts:
            if self._contains_any(message_lower, identity_cues) or self._has_keyword_overlap(message_lower, fact):
                selected.append(f"Stable fact: {fact}")

        for preference in user_memory.preferences:
            if self._contains_any(message_lower, preference_cues) or self._has_keyword_overlap(message_lower, preference):
                selected.append(f"Preference: {preference}")

        for note in user_memory.relationship_notes:
            if self._contains_any(message_lower, relationship_cues) or self._has_keyword_overlap(message_lower, note):
                selected.append(f"Relationship note: {note}")

        if user_memory.conversation_summary and not selected:
            selected.append(f"Summary: {user_memory.conversation_summary}")

        return self._deduplicate_memory_items(selected, limit=5)
    

    def _contains_any(self, text: str, fragments: tuple[str, ...]) -> bool:
        return any(fragment in text for fragment in fragments)
    

    def _has_keyword_overlap(self, message_text: str, memory_text: str) -> bool:
        message_tokens = self._tokenize_for_memory_match(message_text)
        memory_tokens = self._tokenize_for_memory_match(memory_text)
        return bool(message_tokens & memory_tokens)
    

    def _tokenize_for_memory_match(self, text: str) -> set[str]:
        return {
            token
            for token in text.lower().replace(",", " ").replace(".", " ").replace("?", " ").replace("!", " ").split()
            if len(token) >= 4
        }
    

    def _deduplicate_memory_items(self, items: list[str], limit: int) -> list[str]:
        unique_items: list[str] = []

        for item in items:
            if item not in unique_items:
                unique_items.append(item)

        return unique_items[:limit]

        