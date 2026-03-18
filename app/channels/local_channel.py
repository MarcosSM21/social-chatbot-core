from app.orchestrator.chat_orquestrator import ChatOrchestrator

class LocalChannel:
    def __init__(self, orchestrator: ChatOrchestrator) -> None:
        self.orchestrator = orchestrator

    def run(self) -> None:
        print ("Local chat started. Write 'q' to quit." )

        while True:
            user_message = input("You: ").strip()

            if user_message.lower() == "q":
                print("Good bye!")
                break

            response = self.orchestrator.handle_message(user_message)
            print(f"Bot: {response}")