import os 
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    app_env:str
    sqlite_database_path: str
    memory_storage_backend: str
    log_level:str
    llm_provider:str
    internal_api_key: str
    bot_name:str
    bot_enabled : bool
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
    instagram_reply_cooldown_seconds: int
    instagram_allowed_user_ids : list[str]
    instagram_access_token: str
    instagram_app_secret: str
    
    character_file: str





    @classmethod
    def from_env(cls)-> "Settings":
        return cls(
            app_env=os.getenv("APP_ENV", "development"),
            sqlite_database_path = os.getenv("SQLITE_DATABASE_PATH", "data/social_chatbot.sqlite3"),
            memory_storage_backend = os.getenv("MEMORY_STORAGE_BACKEND", "json"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            llm_provider=os.getenv("LLM_PROVIDER", "mock"),
            internal_api_key=os.getenv("INTERNAL_API_KEY", "dev-internal-api-key"),
            bot_name=os.getenv("BOT_NAME", "SocialBot"),
            bot_enabled=os.getenv("BOT_ENABLED", "true").lower() == "true",
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
            instagram_allowed_user_ids=[
                user_id.strip()
                for user_id in os.getenv("INSTAGRAM_ALLOWED_USER_IDS", "").split(",")
                if user_id.strip()
            ],
            instagram_reply_cooldown_seconds=int(os.getenv("INSTAGRAM_REPLY_COOLDOWN_SECONDS", "0")),
            instagram_access_token=os.getenv("INSTAGRAM_ACCESS_TOKEN", os.getenv("INSTAGRAM_TOKEN", "")),
            instagram_app_secret=os.getenv("INSTAGRAM_APP_SECRET", ""),
            character_file=os.getenv("CHARACTER_FILE", "characters/calm_twenty_something.json"),

        )
    
