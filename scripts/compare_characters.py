import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.settings import Settings
from app.engine.response_engine import ResponseEngine
from app.models.chat import ChatMessage
from app.providers.fallback_provider import FallbackGenerationProvider
from app.providers.mock_provider import MockGenerationProvider
from app.providers.ollama_provider import OllamaGenerationProvider
from app.services.assistant_response_safety_validator import AssistantResponseSafetyValidator
from app.services.conversation_context_builder import ConversationContextBuilder
from app.services.conversation_service import ConversationService
from app.services.user_memory_safety_validator import UserMemorySafetyValidator
from app.storage.local_chat_repository import LocalChatRepository
from app.storage.user_memory_repository import UserMemoryRepository


RUNTIME_DIR = Path("evaluation/runtime/character_comparison")
CHAT_HISTORY_FILE = RUNTIME_DIR / "chat_history.json"
USER_MEMORY_FILE = RUNTIME_DIR / "user_memories.json"


def reset_runtime_storage() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    CHAT_HISTORY_FILE.write_text("[]", encoding="utf-8")
    USER_MEMORY_FILE.write_text("[]", encoding="utf-8")

def build_generation_provider(settings: Settings):
    mock_provider = MockGenerationProvider(settings)

    if settings.generation_provider == "ollama":
        ollama_provider = OllamaGenerationProvider(settings)

        if settings.enable_provider_fallback:
            return FallbackGenerationProvider( primary_provider=ollama_provider, fallback_provider=mock_provider)
        
        return ollama_provider
    
    return mock_provider

def build_service(settings:Settings) -> tuple[ConversationService, UserMemoryRepository]:
    user_memory_repository = UserMemoryRepository(str(USER_MEMORY_FILE))
    chat_repository = LocalChatRepository(str(CHAT_HISTORY_FILE))

    service = ConversationService(
        response_engine = ResponseEngine(build_generation_provider(settings)),
        chat_repository=chat_repository,
        context_builder=ConversationContextBuilder(settings, user_memory_repository),
        user_memory_repository=user_memory_repository,
        response_safety_validator=AssistantResponseSafetyValidator(),
        memory_safety_validator=UserMemorySafetyValidator(),
    )

    return service, user_memory_repository

def run_character_case(character_file: str, message: str, provider: str, session_id: str, external_user_id: str) -> dict:
    settings = Settings.from_env()
    settings.character_file = character_file
    settings.generation_provider = provider

    if provider == "ollama":
        settings.enable_provider_fallback = False

    service, user_memory_repository = build_service(settings)

    turn = service.process_message(
        message=ChatMessage(role="user", content=message),
        session_id=session_id,
        platform="instagram",
        external_user_id=external_user_id,
    )

    memory = user_memory_repository.get_or_create(
        platform="instagram",
        external_user_id=external_user_id,
    )

    return {
        "character_file": character_file,
        "character_id": turn.session_metadata.get("character_id"),
        "character_name": turn.session_metadata.get("character_name"),
        "provider": settings.generation_provider,
        "user_message": message,
        "assistant_message": turn.assistant_message.content,
        "memory_after_turn": memory.to_dict(),
        "session_metadata": {
            "memory_loaded": turn.session_metadata.get("memory_loaded"),
            "memory_updated": turn.session_metadata.get("memory_updated"),
            "safety_validation_status": turn.session_metadata.get("safety_validation_status"),
        },
    }


def write_report(results: list[dict]) -> Path:
    reports_dir = Path("evaluation/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_path = reports_dir / "character_comparison_report.json"
    report_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    return report_path

def print_markdown(results: list[dict]) -> None:
    print("# Character Comparison")
    print()

    for result in results:
        print(f"## {result['character_name']} (`{result['character_id']}`)")
        print()
        print(f"- Character file: `{result['character_file']}`")
        print(f"- Provider: `{result['provider']}`")
        print(f"- Memory loaded: `{result['session_metadata']['memory_loaded']}`")
        print(f"- Memory updated: `{result['session_metadata']['memory_updated']}`")
        print(f"- Safety: `{result['session_metadata']['safety_validation_status']}`")
        print()
        print("**User:**")
        print()
        print(result["user_message"])
        print()
        print("**Assistant:**")
        print()
        print(result["assistant_message"])
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare how different characters respond to the same message."
    )
    parser.add_argument("--message", required=True, help="User message to compare.")
    parser.add_argument(
        "--characters",
        nargs="+",
        default=[
            "characters/leo_realistic_friend.json",
            "characters/laia_ambitious_model.json",
        ],
        help="Character JSON files to compare.",
    )
    parser.add_argument(
        "--provider",
        choices=["mock", "ollama"],
        default=os.getenv("EVALUATION_GENERATION_PROVIDER", "mock"),
        help="Generation provider to use.",
    )
    parser.add_argument("--session-id", default="character-comparison-session")
    parser.add_argument("--external-user-id", default="character-comparison-user")
    parser.add_argument(
        "--keep-runtime",
        action="store_true",
        help="Do not reset comparison runtime storage before running.",
    )

    args = parser.parse_args()

    if not args.keep_runtime:
        reset_runtime_storage()

    results = [
        run_character_case(
            character_file=character_file,
            message=args.message,
            provider=args.provider,
            session_id=args.session_id,
            external_user_id=args.external_user_id,
        )
        for character_file in args.characters
    ]

    report_path = write_report(results)
    print_markdown(results)
    print(f"Report written to: {report_path}")


if __name__ == "__main__":
    main()  