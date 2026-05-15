from app.core.settings import Settings
from app.models.chat import ChatMessage, ChatTurn
from app.models.conversation_safety import ConversationSafetyPolicy
from app.models.conversation_context import ConversationContext
from app.storage.user_memory_repository import UserMemoryRepository
from app.models.conversation_character import ConversationCharacter
from app.storage.character_repository import CharacterRepository
from app.models.user_memory import UserMemory
from app.services.language_routing import detect_conversation_language




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

        preferred_language = detect_conversation_language(
            current_message=message.content,
            recent_user_messages=[turn.user_message.content for turn in recent_history],
        )


        retrieved_memory, retrieved_memory_reasons = self._select_relevant_memory(
            user_memory=user_memory,
            current_message=message.content,
        )

        compacted_context = self._build_compacted_turn_context(
            user_memory=user_memory,
            current_message=message.content,
            retrieved_memory=retrieved_memory,
            recent_history=recent_history,
        )

        safety_policy = self._build_safety_policy()
        character = self._build_character()

        return ConversationContext(
            current_message=message,
            recent_history=recent_history,
            system_instructions=self._build_system_instructions(preferred_language),
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
            retrieved_memory_reasons=retrieved_memory_reasons,
            retrieval_strategy="rule_based_memory_selector_v1",
            working_memory_buffer=user_memory.working_memory_buffer,
            compacted_identity_context=compacted_context["identity_context"],
            compacted_preference_context=compacted_context["preference_context"],
            compacted_current_topic_context=compacted_context["current_topic_context"],
            compacted_current_state_context=compacted_context["current_state_context"],
            compacted_relationship_context=compacted_context["relationship_context"],
            compacted_episode_continuity=compacted_context["episode_continuity"],
            compaction_strategy="rule_based_compaction_v1",

        )

    def _build_system_instructions(self, preferred_language: str) -> str:
        if preferred_language == "en":
            language_instruction = (
                "Most important language rule: the user is speaking in English, so you must reply entirely in English. "
                "Keep the whole reply in English, including short reactions, boundaries, flirtation, and casual fillers. "
                "Do not switch to Spanish unless the user clearly switches to Spanish."
            )
        else:
            language_instruction = (
                "Most important language rule: the user is speaking in Spanish, so you must reply entirely in Spanish. "
                "Keep the whole reply in Spanish, including short reactions, boundaries, flirtation, and casual fillers. "
                "Do not switch to English unless the user clearly switches to English."
            )

        return (
            "You are replying in a private chat. "
            "Your conversational identity, voice, and boundaries come from the active character instructions. "
            "Use memory and recent conversation only when relevant. "
            f"{language_instruction}"
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
            "Match the user's language.",
            "If the user writes in English, reply in English.",
            "If the user writes in Spanish, reply in Spanish.",
            "Do not mix Spanish and English unless the user clearly mixes both, and even then prefer the dominant language of the latest user message.",
            "Never describe your own gestures, pauses, facial expressions, or actions.",
            "Never use stage directions or parenthetical action text.",
            "Do not write things like sonrisa leve, pausa, suspira, smiles, or pauses for a moment.",
            "Keep Instagram replies light and socially natural.",
            "Avoid full stops in short replies whenever possible.",
            "Avoid emojis unless they are truly necessary.",
            "Do not sound overly polished, literary, or formally written.",
            "Prefer simple DM phrasing over elegant phrasing.",
            "If the user asks something weird, invasive, or meta, answer briefly and naturally.",
            "If the user asks whether you are an AI, do not deny it.",
            "Admit it briefly in a playful, teasing, lightly amused way.",
            "Do not become technical or explain system details when answering that.",
            "Do not become mystical, conceptual, or poetic when deflecting odd questions.",
            "For probing questions, prefer simple and grounded replies over elegant ones.",
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
    ) -> tuple[list[str], list[str]]:
        
        message_lower = current_message.strip().lower()
        selected: list[str] = []
        reasons: list[str] = []

        identity_cues = ("nombre", "llamo", "name", "remember", "recuerd")
        preference_cues = ("prefiero", "prefer", "gusta", "like", "respuesta", "respond", "tono")
        relationship_cues = ("trato", "hablas", "tono", "broma", "vacil", "sobreexpl")

    

        for fact in user_memory.stable_facts:
            if self._contains_any(message_lower, identity_cues) or self._has_keyword_overlap(message_lower, fact):
                selected.append(f"Stable fact: {fact}")
                reasons.append(f"selected stable_fact because it matched the current message: {fact}")

        for preference in user_memory.preferences:
            if self._contains_any(message_lower, preference_cues) or self._has_keyword_overlap(message_lower, preference):
                selected.append(f"Preference: {preference}")
                reasons.append(f"selected preference because it matched response-style cues: {preference}")

        for note in user_memory.relationship_notes:
            if self._contains_any(message_lower, relationship_cues) or self._has_keyword_overlap(message_lower, note):
                selected.append(f"Relationship note: {note}")
                reasons.append(f"selected relationship_note because it matched relational cues: {note}")

        if not selected and user_memory.user_profile and (
            self._contains_any(message_lower, identity_cues)
            or self._has_keyword_overlap(message_lower, user_memory.user_profile)
        ):
            selected.append(f"Profile: {user_memory.user_profile}")
            reasons.append("selected user_profile as fallback because no structured memory matched first")

        if not selected:
            working_memory_matches = self._select_working_memory_matches(
                working_memory_buffer=user_memory.working_memory_buffer,
                current_message=current_message,
            )
            if working_memory_matches:
                selected.extend(working_memory_matches)
                reasons.append("selected working_memory_buffer because no structured memory matched more strongly")

        if user_memory.conversation_summary and not selected:
            selected.append(f"Summary: {user_memory.conversation_summary}")
            reasons.append("selected conversation_summary as fallback because no other memory source matched")

        selected = self._deduplicate_memory_items(selected, limit=5)
        reasons = self._deduplicate_memory_items(reasons, limit=5)

        return selected, reasons

    

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
    
    def _select_working_memory_matches(self, working_memory_buffer: list[str], current_message: str) -> list[str]:
        if not working_memory_buffer:
            return []
        
        matching_items =  [
            item 
            for item in working_memory_buffer
            if self._has_keyword_overlap(current_message, item)
        ]

        if matching_items:
            return [f"Working memory: {item}" for item in matching_items[-1:]]
        
        return [f"Working memory: {working_memory_buffer[-1]}"]
    


    def _build_compacted_turn_context(
        self,
        user_memory: UserMemory,
        current_message: str,
        retrieved_memory: list[str] | None,
        recent_history: list[ChatTurn],
    ) -> dict[str, list[str] | str | None]:
        identity_context: list[str] = []
        preference_context: list[str] = []
        current_topic_context: list[str] = []
        current_state_context: list[str] = []
        relationship_context: str | None = None
        episode_continuity: str | None = None

        for item in retrieved_memory or []:
            if item.startswith("Stable fact:") or item.startswith("Profile:"):
                identity_context.append(item)

            elif item.startswith("Preference:"):
                preference_context.append(item)

            elif item.startswith("Relationship note:"):
                if relationship_context is None:
                    relationship_context = item

            elif item.startswith("Working memory:") or item.startswith("Summary:"):
                current_topic_context.append(item)

            else: 
                current_topic_context.append(item)

        if not identity_context and user_memory.stable_facts:
            identity_context = [f"Stable fact: {fact}" for fact in user_memory.stable_facts[:2]]

        if not preference_context and user_memory.preferences:
            preference_context = [f"Preference: {preference}" for preference in user_memory.preferences[:2]]

        if not current_topic_context and user_memory.conversation_summary:
            current_topic_context = [f"Summary: {user_memory.conversation_summary}"]

        if user_memory.working_memory_buffer:
            latest_fragment = user_memory.working_memory_buffer[-1]
            if self._looks_like_current_state_fragment(latest_fragment):
                current_state_context = [f"Current state: {latest_fragment}"]

        if recent_history:
            episode_continuity = "continuing_recent_conversation"
        else:
            episode_continuity = "no_recent_history"

        return {
            "identity_context": self._deduplicate_memory_items(identity_context, limit=2),
            "preference_context": self._deduplicate_memory_items(preference_context, limit=2),
            "current_topic_context": self._deduplicate_memory_items(current_topic_context, limit=3),
            "current_state_context": self._deduplicate_memory_items(current_state_context, limit=1),
            "relationship_context": relationship_context,
            "episode_continuity": episode_continuity,
        }
    

    def _looks_like_current_state_fragment(self, text: str) -> bool:
        lowered = text.lower()

        state_cues = (
            "tired",
            "overwhelmed",
            "worried",
            "stressed",
            "blocked",
            "motivated",
            "frustrated",
            "cansado",
            "agobiado",
            "preocup",
            "bloque",
        )

        return any(cue in lowered for cue in state_cues)


        
