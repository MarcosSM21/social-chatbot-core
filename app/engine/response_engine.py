from app.core.settings import Settings


class ResponseEngine:
    def __init__(self, settings: Settings = None) -> None:
        self.setting =  settings

    def generate_response(self, message:str) -> str:
        cleaned_message = message.strip()

        if not cleaned_message:
            return self._empty_message_response()
        
        return self._build_response(cleaned_message)
    

    def _empty_message_response(self) -> str:
        if self.setting.bot_tone == "formal":
            return f"{self.setting.bot_name}: no he recibido ningún mensaje. "
        if self.setting.bot_tone == "direct":
            return f"{self.setting.bot_name}: Mensaje vacío"
        
        return f"{self.setting.bot_name}: no he recibido ningún mensaje.Por favor, envíe algo para que pueda ayudarle."
    
    def _build_response(self, message:str) -> str:
        if self.setting.bot_tone == "formal":
            return f"{self.setting.bot_name}:" f"Hola, he recibido tu mensaje: {message}"
        if self.setting.bot_tone == "direct":
            return f"{self.setting.bot_name}:" f" Recibido: {message}"
        
        return f"{self.setting.bot_name}:" f" Hola, un gusto hablar contigo. Dijiste: {message}"
    
