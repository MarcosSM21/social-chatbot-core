from app.core.settings import Settings
from app.models.chat import ChatMessage, ChatTurn
from app.models.conversation_safety import ConversationSafetyPolicy
from app.models.conversation_context import ConversationContext
from app.storage.user_memory_repository import UserMemoryRepository
from app.models.conversation_character import ConversationCharacter
from app.storage.character_repository import CharacterRepository



class ConversationContextBuilder:
    def __init__(self, settings: Settings, user_memory_repository: UserMemoryRepository, character_repository: CharacterRepository | None = None) -> None:
        self.settings = settings
        self.user_memory_repository = user_memory_repository
        self.character_repository = character_repository or CharacterRepository()

    def build(self, platform: str, external_user_id : str, message: ChatMessage, recent_history: list[ChatTurn] ) -> ConversationContext:

        user_memory = self.user_memory_repository.get_or_create(platform=platform, external_user_id=external_user_id)

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



        