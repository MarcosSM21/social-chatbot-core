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
from app.providers.fallback_provider import FallbackGenerationProvider
from app.providers.mock_provider import MockGenerationProvider
from app.providers.ollama_provider import OllamaGenerationProvider
from app.services.assistant_response_safety_validator import AssistantResponseSafetyValidator
from app.services.conversation_context_builder import ConversationContextBuilder
from app.services.conversation_service import ConversationService
from app.services.memory_summarizer import RuleBasedMemorySummarizer
from app.services.user_memory_safety_validator import UserMemorySafetyValidator
from app.storage.local_chat_repository import LocalChatRepository
from app.storage.user_memory_repository import UserMemoryRepository


CASES_FILE = Path("evaluation/cases/multiturn_conversation_cases.json")
RUNTIME_DIR = Path("evaluation/runtime/multiturn")
REPORTS_DIR = Path("evaluation/reports")

CHAT_HISTORY_FILE = RUNTIME_DIR / "chat_history.json"
USER_MEMORIES_FILE = RUNTIME_DIR / "user_memories.json"

SHORT_RESPONSE_MAX_CHARS = 220


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
                fallback_provider=mock_provider,
            )

        return ollama_provider

    return mock_provider


def build_service(settings: Settings) -> tuple[ConversationService, UserMemoryRepository]:
    user_memory_repository = UserMemoryRepository(str(USER_MEMORIES_FILE))
    chat_repository = LocalChatRepository(str(CHAT_HISTORY_FILE))

    service = ConversationService(
        response_engine=ResponseEngine(build_generation_provider(settings)),
        chat_repository=chat_repository,
        context_builder=ConversationContextBuilder(settings, user_memory_repository),
        user_memory_repository=user_memory_repository,
        response_safety_validator=AssistantResponseSafetyValidator(),
        memory_safety_validator=UserMemorySafetyValidator(),
        memory_summarizer=RuleBasedMemorySummarizer(),
    )

    return service, user_memory_repository


def build_check(name: str, passed: bool, detail: str) -> dict:
    return {
        "name": name,
        "passed": passed,
        "detail": detail,
    }


def contains_any(text: str, fragments: list[str]) -> bool:
    normalized_text = text.lower()
    return any(fragment.lower() in normalized_text for fragment in fragments)


def contains_all(items: list[str], expected_items: list[str]) -> bool:
    normalized_items = [item.lower() for item in items]
    return all(
        any(expected_item.lower() in item for item in normalized_items)
        for expected_item in expected_items
    )


def evaluate_turn(expected_behavior: dict, assistant_message: str, session_metadata: dict) -> dict:
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

    if "should_update_memory" in expected_behavior:
        expected_memory_updated = expected_behavior["should_update_memory"]
        actual_memory_updated = bool(session_metadata.get("memory_updated"))
        checks.append(
            build_check(
                name="should_update_memory",
                passed=actual_memory_updated == expected_memory_updated,
                detail=f"Expected memory_updated={expected_memory_updated}; got {actual_memory_updated}.",
            )
        )

    if "should_store_memory" in expected_behavior:
        expected_store_memory = expected_behavior["should_store_memory"]
        actual_memory_updated = bool(session_metadata.get("memory_updated"))
        checks.append(
            build_check(
                name="should_store_memory",
                passed=actual_memory_updated == expected_store_memory,
                detail=f"Expected memory_updated={expected_store_memory}; got {actual_memory_updated}.",
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


def evaluate_final_memory(expected_final_memory: dict, final_memory: dict | None) -> dict:
    checks: list[dict] = []

    if final_memory is None:
        final_memory = {
            "stable_facts": [],
            "preferences": [],
            "relationship_notes": [],
            "conversation_summary": None,
            "user_profile": None,
        }

    stable_facts = final_memory.get("stable_facts", [])
    preferences = final_memory.get("preferences", [])
    memory_text = json.dumps(final_memory, ensure_ascii=False)

    expected_stable_facts = expected_final_memory.get("stable_facts_should_include", [])
    if expected_stable_facts:
        checks.append(
            build_check(
                name="stable_facts_should_include",
                passed=contains_all(stable_facts, expected_stable_facts),
                detail=f"Expected stable facts to include: {expected_stable_facts}. Got: {stable_facts}.",
            )
        )

    expected_preferences = expected_final_memory.get("preferences_should_include", [])
    if expected_preferences:
        checks.append(
            build_check(
                name="preferences_should_include",
                passed=contains_all(preferences, expected_preferences),
                detail=f"Expected preferences to include: {expected_preferences}. Got: {preferences}.",
            )
        )

    must_not_include = expected_final_memory.get("must_not_include", [])
    if must_not_include:
        checks.append(
            build_check(
                name="final_memory_must_not_include",
                passed=not contains_any(memory_text, must_not_include),
                detail=f"Final memory must not include any of: {must_not_include}.",
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
    turn_results: list[dict] = []

    for index, turn_case in enumerate(case["turns"], start=1):
        turn = service.process_message(
            message=ChatMessage(role="user", content=turn_case["user_message"]),
            session_id=case["session_id"],
            platform=case["platform"],
            external_user_id=case["external_user_id"],
        )

        turn_evaluation = evaluate_turn(
            expected_behavior=turn_case.get("expected_behavior", {}),
            assistant_message=turn.assistant_message.content,
            session_metadata=turn.session_metadata,
        )

        turn_results.append(
            {
                "turn_index": index,
                "user_message": turn_case["user_message"],
                "assistant_message": turn.assistant_message.content,
                "notes": turn_case.get("notes"),
                "session_metadata": turn.session_metadata,
                "evaluation": turn_evaluation,
            }
        )

    final_memory = user_memory_repository.get_by_user(
        platform=case["platform"],
        external_user_id=case["external_user_id"],
    )
    final_memory_dict = final_memory.to_dict() if final_memory else None

    final_memory_evaluation = evaluate_final_memory(
        expected_final_memory=case.get("expected_final_memory", {}),
        final_memory=final_memory_dict,
    )

    passed = all(turn["evaluation"]["passed"] for turn in turn_results) and final_memory_evaluation["passed"]

    return {
        "id": case["id"],
        "title": case["title"],
        "description": case.get("description"),
        "platform": case["platform"],
        "external_user_id": case["external_user_id"],
        "session_id": case["session_id"],
        "passed": passed,
        "turns": turn_results,
        "final_memory": final_memory_dict,
        "final_memory_evaluation": final_memory_evaluation,
    }


def extract_character_summary(results: list[dict]) -> dict:
    for case_result in results:
        for turn in case_result["turns"]:
            metadata = turn.get("session_metadata", {})
            if metadata.get("character_id"):
                return {
                    "character_id": metadata.get("character_id"),
                    "character_name": metadata.get("character_name"),
                    "character_snapshot": metadata.get("character_snapshot"),
                }

    return {
        "character_id": None,
        "character_name": None,
        "character_snapshot": None,
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


def write_json_report(settings: Settings, results: list[dict]) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"multiturn_report_{timestamp}.json"

    passed_cases = sum(1 for result in results if result["passed"])
    failed_cases = len(results) - passed_cases

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "generation_provider": settings.generation_provider,
        "model_provider": build_model_provider_metadata(settings),
        "provider_fallback_enabled": settings.enable_provider_fallback,
        "character": extract_character_summary(results),
        "case_count": len(results),
        "passed_cases": passed_cases,
        "failed_cases": failed_cases,
        "results": results,
    }

    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return report_path


def write_markdown_report(json_report_path: Path, settings: Settings, results: list[dict]) -> Path:
    markdown_path = json_report_path.with_suffix(".md")
    passed_cases = sum(1 for result in results if result["passed"])
    failed_cases = len(results) - passed_cases
    character = extract_character_summary(results)
    model_provider = build_model_provider_metadata(settings)

    lines: list[str] = [
        "# Multiturn Evaluation Report",
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
        f"- Character: `{character.get('character_name')}` (`{character.get('character_id')}`)",
        f"- Total cases: {len(results)}",
        f"- Passed cases: {passed_cases}",
        f"- Failed cases: {failed_cases}",
        "",
        "## Cases",
        "",
    ]

    for result in results:
        case_status = "PASS" if result["passed"] else "FAIL"

        lines.extend(
            [
                f"### {case_status} - {result['id']}",
                "",
                f"**Title:** {result['title']}",
                "",
                f"**Description:** {result.get('description') or ''}",
                "",
            ]
        )

        for turn in result["turns"]:
            turn_status = "PASS" if turn["evaluation"]["passed"] else "FAIL"

            lines.extend(
                [
                    f"#### Turn {turn['turn_index']} - {turn_status}",
                    "",
                    f"**User:** {turn['user_message']}",
                    "",
                    f"**{character.get('character_name') or 'Assistant'}:** {turn['assistant_message']}",
                    "",
                    (
                        f"_memory_loaded={turn['session_metadata'].get('memory_loaded')} | "
                        f"memory_updated={turn['session_metadata'].get('memory_updated')} | "
                        f"profile={turn['session_metadata'].get('memory_profile_status')} | "
                        f"summary={turn['session_metadata'].get('memory_summary_status')} | "
                        f"safety={turn['session_metadata'].get('safety_validation_status')}_"
                    ),
                    "",
                ]
            )

            if turn.get("notes"):
                lines.extend(
                    [
                        f"**Notes:** {turn['notes']}",
                        "",
                    ]
                )


            failed_checks = [
                check
                for check in turn["evaluation"]["checks"]
                if not check["passed"]
            ]

            if failed_checks:
                lines.append("**Failed checks:**")
                lines.append("")
                for check in failed_checks:
                    lines.append(f"- `{check['name']}`: {check['detail']}")
                lines.append("")

        final_memory = result.get("final_memory") or {}

        lines.extend(
            [
                "**Final memory:**",
                "",
                f"- Stable facts: `{final_memory.get('stable_facts', [])}`",
                f"- Preferences: `{final_memory.get('preferences', [])}`",
                f"- Relationship notes: `{final_memory.get('relationship_notes', [])}`",
                f"- Conversation summary: `{final_memory.get('conversation_summary')}`",
                "",
            ]
        )

        final_failed_checks = [
            check
            for check in result["final_memory_evaluation"]["checks"]
            if not check["passed"]
        ]

        if final_failed_checks:
            lines.append("**Final memory failed checks:**")
            lines.append("")
            for check in final_failed_checks:
                lines.append(f"- `{check['name']}`: {check['detail']}")
            lines.append("")

    markdown_path.write_text("\n".join(lines), encoding="utf-8")

    return markdown_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run multiturn conversation evaluation cases.")
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
    parser.add_argument(
        "--keep-runtime",
        action="store_true",
        help="Do not reset multiturn runtime storage before running.",
    )
    args = parser.parse_args()

    if not args.keep_runtime:
        reset_runtime_storage()
    else:
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    settings = Settings.from_env()
    settings.generation_provider = args.provider

    if args.character_file:
        settings.character_file = args.character_file

    if args.provider == "ollama":
        settings.enable_provider_fallback = False

    service, user_memory_repository = build_service(settings)
    cases = load_cases()

    results = [
        run_case(
            case=case,
            service=service,
            user_memory_repository=user_memory_repository,
        )
        for case in cases
    ]

    json_report_path = write_json_report(settings=settings, results=results)
    markdown_report_path = write_markdown_report(
        json_report_path=json_report_path,
        settings=settings,
        results=results,
    )

    print(f"JSON report written to: {json_report_path}")
    print(f"Markdown report written to: {markdown_report_path}")


if __name__ == "__main__":
    main()
