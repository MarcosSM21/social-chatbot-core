import pytest

from app.core.settings import Settings
from app.models.chat import ChatMessage
from app.models.conversation_context import ConversationContext
from app.models.conversation_safety import ConversationSafetyPolicy
from app.models.conversation_character import ConversationCharacter
from app.providers.exceptions import GenerationProviderError
from app.providers.huggingface_local_provider import HuggingFaceLocalGenerationProvider


def test_huggingface_local_provider_is_explicitly_experimental() -> None:
    
    settings = Settings.from_env()
    provider = HuggingFaceLocalGenerationProvider(settings)

    assert provider.model_id == settings.huggingface_model_id
    assert provider.device == settings.huggingface_device
    assert provider.max_new_tokens == settings.huggingface_max_new_tokens
    assert provider.temperature == settings.huggingface_temperature

    context = ConversationContext(
        current_message=ChatMessage(role="user", content="hola"),
        recent_history=[],
        system_instructions="System instructions.",
        safety_instructions="Safety instructions.",
        character_instructions="Character instructions.",
        user_profile=None,
        conversation_summary=None,
        stable_facts=[],
        preferences=[],
        relationship_notes=[],
        safety_policy=ConversationSafetyPolicy.default(),
        character=ConversationCharacter.default(),
    )

    with pytest.raises(GenerationProviderError) as exc_info:
        provider.generate_reply(context)

    assert "experimental" in str(exc_info.value)
    assert "not implemented yet" in str(exc_info.value)
    
