import requests

from app.core.settings import Settings
from app.models.chat import ChatMessage, ChatTurn
from app.providers.exceptions import GenerationProviderError
from app.models.conversation_context import ConversationContext

class LocalLLMGenerationProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.max_history_turns = settings.max_history_turns
        self.timeout_seconds = settings.ollama_timeout_seconds


    def generate_reply(self, context: ConversationContext) -> str:
        messages = self.build_prompt_messages(context)

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            raise GenerationProviderError(f"LLM provider request timed out after {self.timeout_seconds} seconds") from exc
        except requests.ConnectionError as exc:
            raise GenerationProviderError("Could not connect to the local LLM provider") from exc
        except requests.RequestException as exc:
            raise GenerationProviderError(f"Local LLM provider request failed: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise GenerationProviderError("Invalid JSON response from LLM provider") from exc
        
        reply_text = self._extract_reply_text(data)
        if not reply_text:
            raise GenerationProviderError("LLM provider returned an empty reply")
        
        return reply_text
    
    def build_prompt_messages(self, context: ConversationContext) -> list[dict]:
        return self._build_messages(context)
    
    
    
    def _build_messages(self, context: ConversationContext) -> list[dict]:

        messages = [
            {"role": "system", "content": context.system_instructions},
            {"role": "system", "content": context.safety_instructions},
            {"role": "system", "content": context.character_instructions},
            {"role": "system", "content": context.style_instructions},
            ]
        
        if context.user_profile:
            messages.append({"role": "system", "content": f"User profile: {context.user_profile}"})

        if context.stable_facts:
            stable_facts = "\n".join(f"- {fact}" for fact in context.stable_facts)
            messages.append(
                {
                    "role": "system",
                    "content": f"Known stable facts about this user:\n{stable_facts}",
                }
            )

        if context.preferences:
            preferences = "\n".join(f"- {preference}" for preference in context.preferences)
            messages.append(
                {
                    "role": "system",
                    "content": f"Known user preferences:\n{preferences}",
                }
            )

        if context.relationship_notes:
            relationship_notes = "\n".join(f"- {note}" for note in context.relationship_notes)
            messages.append(
                {
                    "role": "system",
                    "content": f"Relationship notes:\n{relationship_notes}",
                }
            )


        if context.conversation_summary:
            messages.append({"role": "system", "content": f"Conversation summary: {context.conversation_summary}"})

        history_messages = self._build_history_messages(context.recent_history)
        messages.extend(history_messages)

        messages.append({"role": "user", "content": context.current_message.content.strip()})

        return messages
    
    
    def _build_history_messages(self, history: list[ChatTurn]) -> list[dict]:
        trimmed_history = history[-self.max_history_turns :]
        messages= []
        
        for turn in trimmed_history:
            messages.append(
                {
                "role": "user",
                "content": turn.user_message.content
                }
            )
            messages.append(
                {
                "role": "assistant",
                "content": turn.assistant_message.content
                }
            )
        return messages
    
    def _extract_reply_text(self, data: dict) -> str:
        message = data.get("message", {})
        content = message.get("content", "")
        return content.strip()