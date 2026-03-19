from app.core.settings import Settings
from app.models.chat import ChatMessage, ChatTurn


class ResponseEngine:
    def __init__(self, settings: Settings = None) -> None:
        self.settings =  settings

    def generate_response(self, message:ChatMessage, history:list[ChatTurn]) -> ChatMessage:
        cleaned_message = message.content.strip()

        if not cleaned_message:
             response_text = self._empty_message_response()
        else:
             response_text= self._build_response(cleaned_message, history)
        return ChatMessage(role="assistant", content=response_text)      
    

    

    def _empty_message_response(self) -> str:
        if self.settings.bot_tone == "formal":
            return f"{self.settings.bot_name}: no he recibido ningún mensaje. "
        if self.settings.bot_tone == "direct":
            return f"{self.settings.bot_name}: Mensaje vacío"
        
        return f"{self.settings.bot_name}: no he recibido ningún mensaje.Por favor, envíe algo para que pueda ayudarle."
    
    def _build_response(self, message:str, history:list[ChatTurn]) -> str:

        has_history = len(history) > 0

        if self.settings.bot_tone == "formal":
            if has_history:
                return (
                    f"{self.settings.bot_name}: "
                    f"We are continuing our conversation. "
                    f"I have received your new message: '{message}'."
                )
            return (
                f"{self.settings.bot_name}: "
                f"Hello. I have received your message: '{message}'."
            )
        
        if self.settings.bot_tone == "direct":
            if has_history:
                return f"{self.settings.bot_name}: Continuing. Received: {message}"
            return f"{self.settings.bot_name}: Received: {message}"

        if has_history:
            return (
                f"{self.settings.bot_name}: "
                f"We are continuing our conversation. You said: {message}"
            )
        
        return f"{self.settings.bot_name}:" f" Hola, un gusto hablar contigo. Dijiste: {message}"
    
