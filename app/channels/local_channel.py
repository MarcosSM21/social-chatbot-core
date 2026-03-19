from app.orchestrator.chat_orquestrator import ChatOrchestrator
from app.core.settings import Settings
from app.models.chat import ChatMessage

class LocalChannel:
    def __init__(self, orchestrator: ChatOrchestrator, settings: Settings, session_id: str) -> None:
        self.orchestrator = orchestrator
        self.settings = settings
        self.session_id = session_id

    def run(self) -> None:
        print (self.settings.bot_welcome_message)

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() == "q":
                print(f"{self.settings.bot_name}: {self.settings.bot_goodbye_message}")
                break

            user_message = ChatMessage(role="user", content=user_input)
            turn = self.orchestrator.handle_message(user_message, self.session_id)
            print(turn.assistant_message.content)