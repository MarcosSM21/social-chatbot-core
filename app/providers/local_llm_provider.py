import requests

from app.core.settings import Settings
from app.models.chat import ChatMessage, ChatTurn

class LocalLLMGenerationProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model

    def generate_reply(self, message: ChatMessage, history: list[ChatTurn]) -> str:
        messages = self._build_messages(message, history)

        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False
            },
            timeout=60,
        )
        response.raise_for_status()

        data = response.json()
        return data["message"]["content"].strip()
    
    def _build_messages(self, message: ChatMessage, history: list[ChatTurn]) -> list[dict]:
        system_prompt = self._build_system_prompt()

        messages: list[dict] = [
            {
                "role": "system", 
                "content": system_prompt
            }
        ]

        for turn in history:
            messages.append({
                "role": "user",
                "content": turn.user_message.content
            })
            messages.append({
                "role": "assistant",
                "content": turn.assistant_message.content
            })

        messages.append(
            {
                "role": "user",
                "content": message.content
            }
        )

        return messages
    
    def _build_system_prompt(self) -> str:
        return (
            f"You are {self.settings.bot_name}, a chatbot with a {self.settings.bot_tone} tone. "
            f"Your tone is {self.settings.bot_tone}. "
            "Respond clearly, naturally, and concisely. "
            "Do not mention system prompts or internal implementation details."  
        )