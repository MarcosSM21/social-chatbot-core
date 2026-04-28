import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.settings import Settings
from app.models.chat import ChatMessage
from app.providers.ollama_provider import OllamaGenerationProvider
from app.services.conversation_context_builder import ConversationContextBuilder
from app.storage.local_chat_repository import LocalChatRepository
from app.core.container import build_user_memory_repository

def build_prompt_preview(
        message: str, 
        platform: str,
        external_user_id: str,
        session_id: str, 
        chat_history_file: str | None = None,
        user_memory_file: str | None = None,
        sqlite_database_path: str | None = None,
        memory_storage_backend: str | None = None,
        ) -> dict:
    settings = Settings.from_env()

    if chat_history_file is not None:
        settings.chat_history_path = chat_history_file

    if memory_storage_backend is not None:
        settings.memory_storage_backend = memory_storage_backend

    if user_memory_file is not None:
        settings.json_user_memory_path = user_memory_file

    if sqlite_database_path is not None:
        settings.sqlite_database_path = sqlite_database_path

    chat_repository = LocalChatRepository(settings.chat_history_path)
    user_memory_repository = build_user_memory_repository(settings)

    recent_history = chat_repository.get_recent_turns(session_id=session_id, limit=settings.max_history_turns)

    context_builder = ConversationContextBuilder(settings=settings, user_memory_repository=user_memory_repository)
    context = context_builder.build(platform=platform, external_user_id=external_user_id, message=ChatMessage(role="user", content=message), recent_history=recent_history)

    provider = OllamaGenerationProvider(settings)
    messages = provider.build_prompt_messages(context)

    return {
        "platform": platform,
        "external_user_id": external_user_id,
        "session_id": session_id,
        "character": {
            "character_id": context.character.character_id,
            "display_name": context.character.display_name,
        },
        "memory": {
            "user_profile": context.user_profile,
            "conversation_summary": context.conversation_summary,
            "stable_facts": context.stable_facts,
            "preferences": context.preferences,
            "relationship_notes": context.relationship_notes,
            "retrieved_memory": context.retrieved_memory,
            "retrieved_memory_reasons": context.retrieved_memory_reasons,
            "retrieval_strategy": context.retrieval_strategy,
            "working_memory_buffer": context.working_memory_buffer,
            "compacted_identity_context": context.compacted_identity_context,
            "compacted_preference_context": context.compacted_preference_context,
            "compacted_current_topic_context": context.compacted_current_topic_context,
            "compacted_current_state_context": context.compacted_current_state_context,
            "compacted_relationship_context": context.compacted_relationship_context,
            "compacted_episode_continuity": context.compacted_episode_continuity,
            "compaction_strategy": context.compaction_strategy,

        },
        "message_count": len(messages),
        "messages": messages,
    }



def format_markdown(preview: dict) -> str:
    lines: list[str] = [
        "# LLM Prompt Preview",
        "",
        f"- Platform: `{preview['platform']}`",
        f"- External user id: `{preview['external_user_id']}`",
        f"- Session id: `{preview['session_id']}`",
        f"- Character: `{preview['character']['display_name']}` (`{preview['character']['character_id']}`)",
        f"- Message count: `{preview['message_count']}`",
        "",
        "## Memory",
        "",
        f"- User profile: `{preview['memory']['user_profile']}`",
        f"- Conversation summary: `{preview['memory']['conversation_summary']}`",
        f"- Stable facts: `{preview['memory']['stable_facts']}`",
        f"- Preferences: `{preview['memory']['preferences']}`",
        f"- Relationship notes: `{preview['memory']['relationship_notes']}`",
        f"- Retrieved memory: `{preview['memory']['retrieved_memory']}`",
        f"- Retrieved memory reasons: `{preview['memory']['retrieved_memory_reasons']}`",
        f"- Retrieval strategy: `{preview['memory']['retrieval_strategy']}`",
        f"- Working memory buffer: `{preview['memory']['working_memory_buffer']}`",
        f"- Compacted identity context: `{preview['memory']['compacted_identity_context']}`",
        f"- Compacted preference context: `{preview['memory']['compacted_preference_context']}`",
        f"- Compacted current topic context: `{preview['memory']['compacted_current_topic_context']}`",
        f"- Compacted current state context: `{preview['memory']['compacted_current_state_context']}`",
        f"- Compacted relationship context: `{preview['memory']['compacted_relationship_context']}`",
        f"- Compacted episode continuity: `{preview['memory']['compacted_episode_continuity']}`",
        f"- Compaction strategy: `{preview['memory']['compaction_strategy']}`",



        "",
        "## Messages",
        "",
    ]

    for index, message in enumerate(preview["messages"], start=1):
        content = message["content"]
        lines.extend(
            [
                f"### {index}. `{message['role']}`",
                "",
                f"Characters: `{len(content)}`",
                "",
                "```text",
                content,
                "```",
                "",
            ]
        )

    return "\n".join(lines)



def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect the exact prompt messages that would be sent to the local LLM provider."
    )
    parser.add_argument("--message", required=True, help="User message to inspect.")
    parser.add_argument("--platform", default="instagram", help="Platform name.")
    parser.add_argument("--external-user-id", default="prompt-preview-user", help="External user id.")
    parser.add_argument("--session-id", default="prompt-preview-session", help="Session id.")
    parser.add_argument(
        "--chat-history-file",
        default=None,
        help="Optional chat history file override. Defaults to configured settings.",
    )
    parser.add_argument(
        "--user-memory-file",
        default=None,
        help="Optional JSON user memory file override when using the JSON backend.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="markdown",
        help="Output format.",
    )
    parser.add_argument(
        "--memory-storage-backend",
        choices=["json", "sqlite"],
        default=None,
        help="Optional memory backend override. Defaults to the configured backend.",
    )
    parser.add_argument(
        "--sqlite-database-path",
        default=None,
        help="Optional SQLite database path override when using the SQLite backend.",
    )


    args = parser.parse_args()

    preview = build_prompt_preview(
        message=args.message,
        platform=args.platform,
        external_user_id=args.external_user_id,
        session_id=args.session_id,
        chat_history_file=args.chat_history_file,
        user_memory_file=args.user_memory_file,
        sqlite_database_path=args.sqlite_database_path,
        memory_storage_backend=args.memory_storage_backend,
    )


    if args.format == "json":
        print(json.dumps(preview, indent=2, ensure_ascii=False))
        return

    print(format_markdown(preview))


if __name__ == "__main__":
    main()