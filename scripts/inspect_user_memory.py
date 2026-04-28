import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.container import build_user_memory_repository
from app.core.settings import Settings


def build_memory_preview(
    platform: str,
    external_user_id: str | None = None,
    *,
    memory_storage_backend: str | None = None,
    sqlite_database_path: str | None = None,
    user_memory_file: str | None = None,
    list_only: bool = False,
) -> dict:
    settings = Settings.from_env()

    if memory_storage_backend is not None:
        settings.memory_storage_backend = memory_storage_backend

    if sqlite_database_path is not None:
        settings.sqlite_database_path = sqlite_database_path

    if user_memory_file is not None:
        settings.json_user_memory_path = user_memory_file

    repository = build_user_memory_repository(settings)

    if list_only:
        memories = repository.list_by_platform(platform)
        return {
            "platform": platform,
            "count": len(memories),
            "memories": [
                {
                    "platform": memory.platform,
                    "external_user_id": memory.external_user_id,
                    "last_known_username": memory.last_known_username,
                    "last_seen_at": memory.last_seen_at,
                    "updated_at": memory.updated_at,
                    "stable_facts_count": len(memory.stable_facts),
                    "preferences_count": len(memory.preferences),
                    "relationship_notes_count": len(memory.relationship_notes),
                    "working_memory_buffer_count": len(memory.working_memory_buffer),
                    "has_conversation_summary": memory.conversation_summary is not None,
                }
                for memory in memories
            ],
        }

    if external_user_id is None:
        raise ValueError("external_user_id is required unless --list is used")

    memory = repository.get_by_user(platform=platform, external_user_id=external_user_id)

    return {
        "platform": platform,
        "external_user_id": external_user_id,
        "found": memory is not None,
        "memory": None
        if memory is None
        else {
            "platform": memory.platform,
            "external_user_id": memory.external_user_id,
            "last_known_username": memory.last_known_username,
            "last_seen_at": memory.last_seen_at,
            "updated_at": memory.updated_at,
            "user_profile": memory.user_profile,
            "stable_facts": memory.stable_facts,
            "preferences": memory.preferences,
            "relationship_notes": memory.relationship_notes,
            "conversation_summary": memory.conversation_summary,
            "working_memory_buffer": memory.working_memory_buffer,
        },
    }


def format_markdown(preview: dict) -> str:
    if "memories" in preview:
        lines = [
            "# User Memory List",
            "",
            f"- Platform: `{preview['platform']}`",
            f"- Count: `{preview['count']}`",
            "",
            "## Memories",
            "",
        ]

        for memory in preview["memories"]:
            lines.extend(
                [
                    f"### `{memory['external_user_id']}`",
                    "",
                    f"- Last known username: `{memory['last_known_username']}`",
                    f"- Last seen at: `{memory['last_seen_at']}`",
                    f"- Updated at: `{memory['updated_at']}`",
                    f"- Stable facts count: `{memory['stable_facts_count']}`",
                    f"- Preferences count: `{memory['preferences_count']}`",
                    f"- Relationship notes count: `{memory['relationship_notes_count']}`",
                    f"- Working memory buffer count: `{memory['working_memory_buffer_count']}`",
                    f"- Has conversation summary: `{memory['has_conversation_summary']}`",
                    "",
                ]
            )

        return "\n".join(lines)

    lines = [
        "# User Memory Preview",
        "",
        f"- Platform: `{preview['platform']}`",
        f"- External user id: `{preview['external_user_id']}`",
        f"- Found: `{preview['found']}`",
        "",
    ]

    memory = preview["memory"]
    if memory is None:
        lines.append("No memory found.")
        return "\n".join(lines)

    lines.extend(
        [
            "## Memory",
            "",
            f"- Last known username: `{memory['last_known_username']}`",
            f"- Last seen at: `{memory['last_seen_at']}`",
            f"- Updated at: `{memory['updated_at']}`",
            f"- User profile: `{memory['user_profile']}`",
            f"- Stable facts: `{memory['stable_facts']}`",
            f"- Preferences: `{memory['preferences']}`",
            f"- Relationship notes: `{memory['relationship_notes']}`",
            f"- Conversation summary: `{memory['conversation_summary']}`",
            f"- Working memory buffer: `{memory['working_memory_buffer']}`",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect stored user memory using the configured memory backend."
    )
    parser.add_argument("--platform", required=True, help="Platform name.")
    parser.add_argument("--external-user-id", default=None, help="External user id.")
    parser.add_argument("--list", action="store_true", help="List memories for a platform.")
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
        help="Optional memory backend override.",
    )
    parser.add_argument(
        "--sqlite-database-path",
        default=None,
        help="Optional SQLite database path override.",
    )
    parser.add_argument(
        "--user-memory-file",
        default=None,
        help="Optional JSON user memory file override.",
    )

    args = parser.parse_args()

    preview = build_memory_preview(
        platform=args.platform,
        external_user_id=args.external_user_id,
        memory_storage_backend=args.memory_storage_backend,
        sqlite_database_path=args.sqlite_database_path,
        user_memory_file=args.user_memory_file,
        list_only=args.list,
    )

    if args.format == "json":
        print(json.dumps(preview, indent=2, ensure_ascii=False))
        return

    print(format_markdown(preview))


if __name__ == "__main__":
    main()
