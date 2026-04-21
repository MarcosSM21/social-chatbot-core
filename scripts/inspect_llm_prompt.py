import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.settings import Settings
from app.models.chat import ChatMessage
from app.providers.local_llm_provider import LocalLLMGenerationProvider
from app.services.conversation_context_builder import ConversationContextBuilder
from app.storage.local_chat_repository import LocalChatRepository
from app.storage.user_memory_repository import UserMemoryRepository

def build_prompt_preview(message: str, platform: str, external_user_id: str, session_id: str, chat_history_file: str, user_memory_file: str) -> dict:
    settings = Settings.from_env()

    chat_repository = LocalChatRepository(chat_history_file)
    user_memory_repository = UserMemoryRepository(user_memory_file)

    recent_history = chat_repository.get_recent_turns(session_id=session_id, limit=settings.max_history_turns)

    context_builder = ConversationContextBuilder(settings=settings, user_memory_repository=user_memory_repository)
    context = context_builder.build(platform=platform, external_user_id=external_user_id, message=ChatMessage(role="user", content=message), recent_history=recent_history)

    provider = LocalLLMGenerationProvider(settings)
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
            "relationship_notes": context.relationship_notes
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
    parser.add_argument("--chat-history-file", default="data/chat_history.json", help="Chat history file.")
    parser.add_argument("--user-memory-file", default="data/user_memories.json", help="User memory file.")
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="markdown",
        help="Output format.",
    )

    args = parser.parse_args()

    preview = build_prompt_preview(
        message=args.message,
        platform=args.platform,
        external_user_id=args.external_user_id,
        session_id=args.session_id,
        chat_history_file=args.chat_history_file,
        user_memory_file=args.user_memory_file,
    )

    if args.format == "json":
        print(json.dumps(preview, indent=2, ensure_ascii=False))
        return

    print(format_markdown(preview))


if __name__ == "__main__":
    main()