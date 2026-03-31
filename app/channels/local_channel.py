from app.orchestrator.chat_orquestrator import ChatOrchestrator
from app.core.settings import Settings
from app.models.chat import ChatMessage

class LocalChannel:
    """Terminal-based implementation of a channel adapter"""

    def __init__(self, orchestrator: ChatOrchestrator, settings: Settings, session_id: str) -> None:
        self.orchestrator = orchestrator
        self.settings = settings
        self.session_id = session_id

    def run(self) -> None:
        self._print_welcome()

        try:
            while True:
                try:
                    user_input = input("You: ").strip()
                except EOFError:
                    print()
                    print(f"{self.settings.bot_name}: End of input detected. Ending session.")

                if not user_input:
                    print(f"{self.settings.bot_name}: Escribe algo cabezón")
                    continue

                command_result = self._handle_command(user_input)
                if command_result == "exit":
                    break
                elif command_result == "continue":
                    continue

                user_message = ChatMessage(role="user", content=user_input)
                turn = self.orchestrator.handle_message(user_message, self.session_id, platform="local", external_user_id=self.session_id)
                print(f"LLM:{turn.assistant_message.content}")
        
        except KeyboardInterrupt:
            print()
            print(f"{self.settings.bot_name}: Sesión terminada por el usuario. ¡Hasta luego!")

        
    def _print_welcome(self) -> None:
        print(f"{self.settings.bot_name}: {self.settings.bot_welcome_message}")
        print(f"Session ID: {self.session_id}")
        print("Type 'help' to see available commands.")

    def _handle_command(self, user_input: str) -> bool:
        normalized = user_input.lower()

        if normalized == "q":
            print(f"{self.settings.bot_name}: {self.settings.bot_goodbye_message}")
            return "exit"
        
        if normalized == "help":
            self._print_help()
            return "continue"
        
        if normalized == "session":
            self._print_session()
            return "continue"

        if normalized == "history":
            self._print_history()
            return "continue"
        
        return None
    
    def _print_help(self) -> None:
        print("Available commands:")
        print("  help    - show available commands")
        print("  session - show current session id")
        print("  history - show recent session history")
        print("  q   - quit the local chat")

    def _print_session(self) -> None:
        print(f"Current session ID: {self.session_id}")

    def _print_history(self) -> None:
        print("-" * 40)
        history = self.orchestrator.get_session_history(self.session_id, limit=3)
        

        if not history:
            print(f"{self.settings.bot_name}: No hay historial para esta sesión.")
            return
        
        print("Recent session history:")
        for index, turn in enumerate(history, start=1):
            print(f"Turn {index}:")
            print(f"  You: {turn.user_message.content}")
            print(f"  LLM:{turn.assistant_message.content}")
            print("-" * 40)

        