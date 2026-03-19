import uuid

from app.core.settings import Settings

from app.channels.local_channel import LocalChannel
from app.orchestrator.chat_orquestrator import ChatOrchestrator
from app.engine.response_engine import ResponseEngine
from app.storage.local_chat_repository import LocalChatRepository
from app.services.conversation_service import ConversationService
from app.core.container import build_local_channel


class Application:
    def __init__(self, settings: Settings):
        self.settings = settings

    def run(self) -> None:
        print("social-chatbot-core initialized")
        print(f"Environment: {self.settings.app_env}")
        print(f"Log level: {self.settings.log_level}")
        print(f"LLM Provider: {self.settings.llm_provider}")
        print(f"Bot Name: {self.settings.bot_name}")
        print(f"Bot Tone: {self.settings.bot_tone}")

        local_channel = build_local_channel(self.settings)

        local_channel.run()

        