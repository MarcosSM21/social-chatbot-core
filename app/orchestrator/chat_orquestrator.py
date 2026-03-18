from app.engine.response_engine import ResponseEngine

class ChatOrchestrator:
    def __init__(self, response_engine: ResponseEngine) -> None:
        self.response_engine = response_engine

    def handle_message(self, message: str) -> str:
        return self.response_engine.generate_response(message)