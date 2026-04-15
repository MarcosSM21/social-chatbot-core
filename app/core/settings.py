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
    max_history_turns: int
    ollama_timeout_seconds: int
    enable_provider_fallback : bool
    webhook_verify_token: str
    instagram_api_version: str
    instagram_ig_user_id: str
    instagram_access_token: str
    instagram_app_secret: str
    
    character_file: str

    style_persona_hint: str
    style_tone: str
    style_response_length: str
    style_directness: str
    style_warmth: str
    style_formality: str
    style_rhythm: str
    style_empathy: str
    style_preset: str


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
            ollama_model=os.getenv("OLLAMA_MODEL", "gemma3"),
            max_history_turns=int(os.getenv("MAX_HISTORY_TURNS", "3")),
            ollama_timeout_seconds=int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60")),
            enable_provider_fallback=os.getenv("ENABLE_PROVIDER_FALLBACK", "true").lower() == "true",
            webhook_verify_token=os.getenv("WEBHOOK_VERIFY_TOKEN", "dev-verify-token"),
            instagram_api_version=os.getenv("INSTAGRAM_API_VERSION", "v24.0"),
            instagram_ig_user_id=os.getenv("INSTAGRAM_IG_USER_ID", ""),
            instagram_access_token=os.getenv("INSTAGRAM_ACCESS_TOKEN", os.getenv("INSTAGRAM_TOKEN", "")),
            instagram_app_secret=os.getenv("INSTAGRAM_APP_SECRET", ""),
            character_file=os.getenv("CHARACTER_FILE", "characters/calm_twenty_something.json"),
            style_preset=os.getenv("STYLE_PRESET", "short_direct_calm"),
            style_persona_hint=os.getenv("STYLE_PERSONA_HINT", ""),
            style_tone=os.getenv("STYLE_TONE", ""),
            style_response_length=os.getenv("STYLE_RESPONSE_LENGTH", ""),
            style_directness=os.getenv("STYLE_DIRECTNESS", ""),
            style_warmth=os.getenv("STYLE_WARMTH", ""),
            style_formality=os.getenv("STYLE_FORMALITY", ""),
            style_rhythm=os.getenv("STYLE_RHYTHM", ""),
            style_empathy=os.getenv("STYLE_EMPATHY", ""),

        )
    
