from app.core.settings import Settings
from app.models.conversation_context import ConversationContext
from app.providers.exceptions import GenerationProviderError

class HuggingFaceLocalGenerationProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model_id = settings.huggingface_model_id
        self.device = settings.huggingface_device
        self.max_new_tokens = settings.huggingface_max_new_tokens
        self.temperature = settings.huggingface_temperature

    def generate_reply(self, context: ConversationContext) -> str:
        raise GenerationProviderError(
            "HuggingFaceLocalGenerationProvider is experimental and not implemented yet."
            "Install optional Hugging Face dependencies and implement local inference before using it."
        )
    
    