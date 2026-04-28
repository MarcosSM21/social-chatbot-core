import requests

from app.core.settings import Settings
from app.models.chat import ChatMessage, ChatTurn
from app.providers.exceptions import GenerationProviderError
from app.models.conversation_context import ConversationContext

class OllamaGenerationProvider:
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
            raise GenerationProviderError(f"Ollama request timed out after {self.timeout_seconds} seconds") from exc
        except requests.ConnectionError as exc:
            raise GenerationProviderError("Could not connect to the local Ollama provider") from exc
        except requests.RequestException as exc:
            raise GenerationProviderError(f"Ollama provider request failed: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise GenerationProviderError("Invalid JSON response from Ollama provider") from exc
        
        reply_text = self._extract_reply_text(data)
        if not reply_text:
            raise GenerationProviderError("Ollama provider returned an empty reply")
        
        return reply_text
    
    def build_prompt_messages(self, context: ConversationContext) -> list[dict]:
        return self._build_messages(context)
    
    
    
    def _build_messages(self, context: ConversationContext) -> list[dict]:

        messages = [
            {"role": "system", "content": context.system_instructions},
            {"role": "system", "content": context.safety_instructions},
            {"role": "system", "content": context.character_instructions},
            ]
        
        compacted_sections: list[str] = []

        if context.compacted_identity_context:
            compacted_sections.append(
                "Identity context:\n" + "\n".join(f"- {item}" for item in context.compacted_identity_context)
            )

        if context.compacted_preference_context:
            compacted_sections.append(
                "Preference context:\n" + "\n".join(f"- {item}" for item in context.compacted_preference_context)
            )

        if context.compacted_current_topic_context:
            compacted_sections.append(
                "Current topic context:\n" + "\n".join(f"- {item}" for item in context.compacted_current_topic_context)
            )

        if context.compacted_current_state_context:
            compacted_sections.append(
                "Current state context:\n" + "\n".join(f"- {item}" for item in context.compacted_current_state_context)
            )

        if context.compacted_relationship_context:
            compacted_sections.append(
                f"Relationship context:\n- {context.compacted_relationship_context}"
            )

        if context.compacted_episode_continuity:
            compacted_sections.append(
                f"Episode continuity:\n- {context.compacted_episode_continuity}"
            )

        if compacted_sections:
            messages.append(
                {
                    "role": "system",
                    "content": "Compacted turn context:\n\n" + "\n\n".join(compacted_sections),
                }
            )


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