from app.channels.local_channel import LocalChannel
from app.orchestrator.chat_orquestrator import ChatOrchestrator
from app.engine.response_engine import ResponseEngine

from app.core.settings import Settings

class Application:
    def __init__(self, settings: Settings):
        self.settings = settings

    def run(self) -> None:
        print("social-chatbot-core initialized")
        print(f"Environment: {self.settings.app_env}")
        print(f"Log level: {self.settings.log_level}")
        print(f"LLM Provider: {self.settings.llm_provider}")

        response_engine = ResponseEngine()
        orchestrator = ChatOrchestrator(response_engine)
        local_channel = LocalChannel(orchestrator)

        local_channel.run()

        