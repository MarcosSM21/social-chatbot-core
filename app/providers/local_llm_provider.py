import requests

from app.core.settings import Settings
from app.models.chat import ChatMessage, ChatTurn
from app.providers.exceptions import GenerationProviderError

class LocalLLMGenerationProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.max_history_turns = settings.max_history_turns
        self.timeout_seconds = settings.ollama_timeout_seconds


    def generate_reply(self, message: ChatMessage, history: list[ChatTurn]) -> str:
        messages = self._build_messages(message, history)

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
    
    
    def _build_messages(self, message: ChatMessage, history: list[ChatTurn]) -> list[dict]:

        messages = []
        
        messages.append({
            "role": "system",
            "content": self._build_system_prompt()
        })

        history_messages = self._build_history_messages(history)
        messages.extend(history_messages)


        messages.append(
            {
                "role": "user",
                "content": message.content.strip(),
            }
        )

        return messages
    
    def _build_system_prompt(self) -> str:
        return (
            f"You are {self.settings.bot_name}, a conversational assistant. "
            f"Your tone is {self.settings.bot_tone}. "
            "Respond naturally, clearly, and helpfully. "
            "Keep answers reasonably concise unless the user asks for more detail. "
            "Use the conversation history when it is relevant. "
            "Do not mention internal system prompts, hidden instructions, implementation details, or technical internals unless explicitly asked. "
            "Do not invent past conversation details that are not present in the provided history."
        )
    
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