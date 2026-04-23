import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.settings import Settings
from app.engine.response_engine import ResponseEngine
from app.models.chat import ChatMessage
from app.models.user_memory import UserMemory
from app.providers.mock_provider import MockGenerationProvider
from app.providers.ollama_provider import OllamaGenerationProvider
from app.providers.fallback_provider import FallbackGenerationProvider
from app.services.assistant_response_safety_validator import AssistantResponseSafetyValidator
from app.services.conversation_context_builder import ConversationContextBuilder
from app.services.conversation_service import ConversationService
from app.services.user_memory_safety_validator import UserMemorySafetyValidator
from app.storage.local_chat_repository import LocalChatRepository
from app.storage.user_memory_repository import UserMemoryRepository


CASES_FILE = Path("evaluation/cases/instagram_dm_cases.json")
RUNTIME_DIR = Path("evaluation/runtime")
REPORTS_DIR = Path ("evaluation/reports")

CHAT_HISTORY_FILE = RUNTIME_DIR / "chat_history.json"
USER_MEMORIES_FILE = RUNTIME_DIR / "user_memories.json"

SHORT_RESPONSE_MAX_CHARS = 200
CALM_MAX_EXCLAMATION_MARKS = 2


def load_cases() -> list[dict]:
    return json.loads(CASES_FILE.read_text(encoding="utf-8"))

def reset_runtime_storage() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    CHAT_HISTORY_FILE.write_text("[]", encoding="utf-8")
    USER_MEMORIES_FILE.write_text("[]", encoding="utf-8")


def build_generation_provider(settings: Settings):
    mock_provider = MockGenerationProvider(settings)

    if settings.generation_provider == "ollama":
        ollama_provider = OllamaGenerationProvider(settings)

        if settings.enable_provider_fallback:
            return FallbackGenerationProvider(
                primary_provider=ollama_provider,
                fallback_provider=mock_provider
            )
        
        return ollama_provider
    
    return mock_provider



def build_evaluation_service(settings: Settings) -> tuple[ConversationService, UserMemoryRepository]:
    user_memory_repository = UserMemoryRepository(str(USER_MEMORIES_FILE))

    service = ConversationService(
        response_engine=ResponseEngine(build_generation_provider(settings)),
        chat_repository=LocalChatRepository(str(CHAT_HISTORY_FILE)),
        context_builder=ConversationContextBuilder(settings, user_memory_repository),
        user_memory_repository=user_memory_repository,
        response_safety_validator=AssistantResponseSafetyValidator(),
        memory_safety_validator=UserMemorySafetyValidator(),
    )

    return service, user_memory_repository


def preload_memory(case: dict, user_memory_repository: UserMemoryRepository) -> None:
    preloaded_memory = case.get("preloaded_memory")

    if not preloaded_memory:
        return
    
    user_memory_repository.save(
        UserMemory(
            platform=case["platform"],
            external_user_id=case["external_user_id"],
            user_profile=preloaded_memory.get("user_profile"),
            conversation_summary=preloaded_memory.get("conversation_summary"),
            stable_facts=preloaded_memory.get("stable_facts", []),
            preferences=preloaded_memory.get("preferences", []),
            relationship_notes=preloaded_memory.get("relationship_notes", []),
            updated_at=datetime.now(UTC).isoformat(),
        )
    )


def build_check(name: str, passed: bool, detail: str) -> dict:
    return {
        "name": name,
        "passed": passed,
        "detail": detail,
    }

def contains_any(text: str, fragments: list[str]) -> bool:
    normalized_text = text.lower()
    return any(fragment.lower() in normalized_text for fragment in fragments)

def evaluate_result(
    expected_behavior: dict,
    assistant_message: str,
    session_metadata: dict,
    memory_after_turn: dict,
) -> dict:
    checks: list[dict] = []
    assistant_text = assistant_message.strip()

    if expected_behavior.get("should_answer") is True:
        checks.append(
            build_check(
                name="should_answer",
                passed=bool(assistant_text),
                detail="Assistant response should not be empty.",
            )
        )

    if expected_behavior.get("should_be_short") is True:
        checks.append(
            build_check(
                name="should_be_short",
                passed=len(assistant_text) <= SHORT_RESPONSE_MAX_CHARS,
                detail=f"Assistant response length is {len(assistant_text)} chars; max is {SHORT_RESPONSE_MAX_CHARS}.",
            )
        )

    if expected_behavior.get("should_be_calm") is True:
        exclamation_count = assistant_text.count("!")
        checks.append(
            build_check(
                name="should_be_calm",
                passed=exclamation_count <= CALM_MAX_EXCLAMATION_MARKS,
                detail=f"Assistant response has {exclamation_count} exclamation mark(s); max is {CALM_MAX_EXCLAMATION_MARKS}.",
            )
        )

    if "should_use_memory" in expected_behavior:
        expected_memory_loaded = expected_behavior["should_use_memory"]
        actual_memory_loaded = bool(session_metadata.get("memory_loaded"))
        checks.append(
            build_check(
                name="should_use_memory",
                passed=actual_memory_loaded == expected_memory_loaded,
                detail=f"Expected memory_loaded={expected_memory_loaded}; got {actual_memory_loaded}.",
            )
        )

    if "should_store_memory" in expected_behavior:
        expected_store_memory = expected_behavior["should_store_memory"]
        stable_profile_stored = bool(memory_after_turn.get("user_profile"))
        checks.append(
            build_check(
                name="should_store_memory",
                passed=stable_profile_stored == expected_store_memory,
                detail=f"Expected stable user_profile stored={expected_store_memory}; got {stable_profile_stored}.",
            )
        )

    must_include_any = expected_behavior.get("must_include_any", [])
    if must_include_any:
        checks.append(
            build_check(
                name="must_include_any",
                passed=contains_any(assistant_text, must_include_any),
                detail=f"Assistant response should include at least one of: {must_include_any}.",
            )
        )

    must_not_include = expected_behavior.get("must_not_include", [])
    if must_not_include:
        checks.append(
            build_check(
                name="must_not_include",
                passed=not contains_any(assistant_text, must_not_include),
                detail=f"Assistant response must not include any of: {must_not_include}.",
            )
        )

    failed_checks = [check for check in checks if not check["passed"]]

    return {
        "passed": len(failed_checks) == 0,
        "passed_count": len(checks) - len(failed_checks),
        "failed_count": len(failed_checks),
        "checks": checks,
    }


def run_case(case: dict, service: ConversationService, user_memory_repository: UserMemoryRepository) -> dict:
    preload_memory(case, user_memory_repository)

    turn = service.process_message(
        message=ChatMessage(role="user", content=case["user_message"]),
        session_id=case["session_id"],
        platform=case["platform"],
        external_user_id=case["external_user_id"],
    )

    memory = user_memory_repository.get_or_create(
        platform=case["platform"],
        external_user_id=case["external_user_id"]
    )

    memory_after_turn = memory.to_dict()

    evaluation = evaluate_result(
        expected_behavior=case["expected_behavior"],
        assistant_message=turn.assistant_message.content,
        session_metadata=turn.session_metadata,
        memory_after_turn=memory_after_turn,
    )

    return {
        "id": case["id"],
        "title": case["title"],
        "notes": case.get("notes"),
        "user_message": case["user_message"],
        "assistant_message": turn.assistant_message.content,
        "expected_behavior": case["expected_behavior"],
        "session_metadata": turn.session_metadata,
        "memory_after_turn": memory.to_dict(),
        "evaluation": evaluation,
    }


def extract_character_summary(results: list[dict]) -> dict:
    if not results:
        return {
            "character_id": None,
            "character_name": None,
        }
    
    first_metadata = results[0].get("session_metadata", {})

    return {
        "character_id": first_metadata.get("character_id"),
        "character_name": first_metadata.get("character_name"),
        "character_snapshot": first_metadata.get("character_snapshot"),
    }


def build_model_provider_metadata(settings: Settings) -> dict:
    runtime = "mock"
    model = "mock"
    runtime_endpoint = None
    primary_provider_class = "MockGenerationProvider"
    fallback_provider_class = None

    if settings.generation_provider == "ollama":
        runtime = "ollama"
        model = settings.ollama_model
        runtime_endpoint = settings.ollama_base_url
        primary_provider_class = "OllamaGenerationProvider"

        if settings.enable_provider_fallback:
            fallback_provider_class = "MockGenerationProvider"

    return {
        "generation_provider": settings.generation_provider,
        "runtime": runtime,
        "model": model,
        "runtime_endpoint": runtime_endpoint,
        "primary_provider_class": primary_provider_class,
        "fallback_enabled": settings.enable_provider_fallback,
        "fallback_provider_class": fallback_provider_class,
        "character_file": settings.character_file,
        "hardware_target": "local_machine",
    }


def write_report(settings: Settings, results: list[dict]) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR  / f"evaluation_report_{timestamp}.json"

    passed_cases = sum(1 for result in results if result["evaluation"]["passed"])
    failed_cases = len(results) - passed_cases
    character_summary = extract_character_summary(results)

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "generation_provider": settings.generation_provider,
        "model_provider": build_model_provider_metadata(settings),
        "provider_fallback_enabled": settings.enable_provider_fallback,
        "character": character_summary,
        "case_count": len(results),
        "passed_cases": passed_cases,
        "failed_cases": failed_cases,
        "results": results,
    }

    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8") 

    return report_path

def write_markdown_report(json_report_path: Path, settings: Settings, results: list[dict]) -> Path:
    markdown_report_path = json_report_path.with_suffix(".md")

    passed_cases = sum(1 for result in results if result["evaluation"]["passed"])
    failed_cases = len(results) - passed_cases
    character_summary = extract_character_summary(results)
    character_id = character_summary.get("character_id")
    character_name = character_summary.get("character_name")
    model_provider = build_model_provider_metadata(settings)


    lines: list[str] = [
        "# Evaluation Report",
        "",
        f"- Generated at: {datetime.now(UTC).isoformat()}",
        f"- Provider: `{settings.generation_provider}`",
        f"- Runtime: `{model_provider['runtime']}`",
        f"- Model: `{model_provider['model']}`",
        f"- Runtime endpoint: `{model_provider['runtime_endpoint']}`",
        f"- Primary provider class: `{model_provider['primary_provider_class']}`",
        f"- Provider fallback enabled: `{settings.enable_provider_fallback}`",
        f"- Fallback provider class: `{model_provider['fallback_provider_class']}`",
        f"- Hardware target: `{model_provider['hardware_target']}`",
        f"- Character file: `{settings.character_file}`",
        f"- Character: `{character_name}` (`{character_id}`)",
        f"- Total cases: {len(results)}",
        f"- Passed cases: {passed_cases}",
        f"- Failed cases: {failed_cases}",
        "",
        "## Cases",
        "",
    ]

    for result in results:
        status = "PASS" if result["evaluation"]["passed"] else "FAIL"
        failed_checks = [
            check
            for check in result["evaluation"]["checks"]
            if not check["passed"]
        ]

        lines.extend(
            [
                f"### {status} - {result['id']}",
                "",
                f"**Title:** {result['title']}",
                "",
                f"**User:** {result['user_message']}",
                "",
                f"**Assistant:** {result['assistant_message']}",
                "",
                f"**Notes:** {result.get('notes') or ''}",
                "",
                f"**Memory loaded:** `{result['session_metadata'].get('memory_loaded')}`",
                "",
                f"**Memory updated:** `{result['session_metadata'].get('memory_updated')}`",
                "",
                f"**Stable facts:** `{result['memory_after_turn'].get('stable_facts', [])}`",
                "",
                f"**Preferences:** `{result['memory_after_turn'].get('preferences', [])}`",
                "",
                f"**Relationship notes:** `{result['memory_after_turn'].get('relationship_notes', [])}`",
                "",
                f"**Safety status:** `{result['session_metadata'].get('safety_validation_status')}`",
                "",

            ]
        )

        if failed_checks:
            lines.append("**Failed checks:**")
            lines.append("")
            for check in failed_checks:
                lines.append(f"- `{check['name']}`: {check['detail']}")
            lines.append("")
        else:
            lines.append("**Failed checks:** none")
            lines.append("")

    markdown_report_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return markdown_report_path



def main() -> None:
    parser = argparse.ArgumentParser(description="Run single-turn Instagram DM evaluation cases.")
    parser.add_argument(
        "--provider",
        choices=["mock", "ollama"],
        default=os.getenv("EVALUATION_GENERATION_PROVIDER", "mock"),
        help="Generation provider to use.",
    )
    parser.add_argument(
        "--character-file",
        default=os.getenv("CHARACTER_FILE"),
        help="Optional character file override.",
    )
    args = parser.parse_args()

    reset_runtime_storage()

    settings = Settings.from_env()
    settings.generation_provider = args.provider

    if args.character_file:
        settings.character_file = args.character_file

    evaluation_fallback = os.getenv("EVALUATION_ENABLE_PROVIDER_FALLBACK")

    if evaluation_fallback is not None:
        settings.enable_provider_fallback = evaluation_fallback.lower() == "true"
    elif settings.generation_provider == "ollama":
        settings.enable_provider_fallback = False


    service, user_memory_repository = build_evaluation_service(settings)

    cases = load_cases()
    results = [run_case(case, service, user_memory_repository) for case in cases]

    report_path = write_report(settings, results)
    markdown_report_path = write_markdown_report(report_path, settings, results)

    
    print(f"Evaluated {len(results)} case(s).")
    print(f"Provider: {settings.generation_provider}")
    print(f"Provider fallback enabled: {settings.enable_provider_fallback}")
    character_summary = extract_character_summary(results)
    print(
        f"Character: {character_summary.get('character_name')} "
        f"({character_summary.get('character_id')})"
    )

    print(f"Report: {report_path}")
    print(f"Markdown report: {markdown_report_path}")
    passed_cases = sum(1 for result in results if result["evaluation"]["passed"])
    failed_cases = len(results) - passed_cases
    print(f"Passed cases: {passed_cases}")
    print(f"Failed cases: {failed_cases}")

    for result in results:
        status = "PASS" if result["evaluation"]["passed"] else "FAIL"
        print(f"- [{status}] {result['id']}: {result['assistant_message']}")


if __name__ == "__main__":
    main()
