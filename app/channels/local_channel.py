from app.orchestrator.chat_orquestrator import ChatOrchestrator
from app.core.settings import Settings

class LocalChannel:
    def __init__(self, orchestrator: ChatOrchestrator, settings: Settings) -> None:
        self.orchestrator = orchestrator
        self.settings = settings 

    def run(self) -> None:
        print (self.settings.bot_welcome_message)

        while True:
            user_message = input("You: ").strip()

            if user_message.lower() == "q":
                print(f"{self.settings.bot_name}: {self.settings.bot_goodbye_message}")
                break

            response = self.orchestrator.handle_message(user_message)
            print(response)