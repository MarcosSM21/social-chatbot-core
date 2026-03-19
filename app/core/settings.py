import os 
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    app_env:str
    log_level:str
    llm_provider:str
    bot_name:str
    bot_tone: str
    bot_welcome_message: str
    bot_goodbye_message: str
    generation_provider: str 
    ollama_base_url: str
    ollama_model: str

    @classmethod
    def from_env(cls)-> "Settings":
        return cls(
            app_env=os.getenv("APP_ENV", "development"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            llm_provider=os.getenv("LLM_PROVIDER", "mock"),
            bot_name=os.getenv("BOT_NAME", "SocialBot"),
            bot_tone=os.getenv("BOT_TONE", "friendly"),
            bot_welcome_message=os.getenv("BOT_WELCOME_MESSAGE", 
                                          "¡Hola! Soy Social, escribe 'q' para salir"),
            bot_goodbye_message=os.getenv("BOT_GOODBYE_MESSAGE", "¡Adiós!"),
            generation_provider=os.getenv("GENERATION_PROVIDER", "mock"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "gemma3")
        )
    
