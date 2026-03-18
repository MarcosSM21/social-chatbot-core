from app.core.settings import Settings

class Application:
    def __init__(self, settings: Settings):
        self.settings = settings

    def run(self) -> None:
        print("social-chatbot-core initialized")
        print(f"Environment: {self.settings.app_env}")
        print(f"Log level: {self.settings.log_level}")
        print(f"LLM Provider: {self.settings.llm_provider}")

        