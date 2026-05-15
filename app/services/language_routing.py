def detect_conversation_language(
    current_message: str,
    recent_user_messages: list[str] | None = None,
) -> str:
    recent_user_messages = recent_user_messages or []
    latest_text = (current_message or "").strip().lower()

    if _looks_english(latest_text):
        return "en"

    if _looks_spanish(latest_text):
        return "es"

    combined_recent = " ".join(message.strip().lower() for message in recent_user_messages)

    if _looks_english(combined_recent):
        return "en"

    return "es"


def _looks_english(text: str) -> bool:
    if not text:
        return False

    english_markers = (
        " the ",
        " and ",
        " you ",
        " your ",
        "what",
        "hello",
        "hi ",
        " are ",
        " is ",
        " do ",
        " why ",
        " how ",
        "thanks",
        "please",
        "beautiful",
        "honestly",
    )
    padded = f" {text} "
    return any(marker in padded for marker in english_markers)


def _looks_spanish(text: str) -> bool:
    if not text:
        return False

    spanish_markers = (
        " que ",
        "hola",
        "gracias",
        " por ",
        " para ",
        " como ",
        " estás",
        " estoy",
        "prefiero",
        "hablar",
        " contigo",
    )
    padded = f" {text} "
    return any(marker in padded for marker in spanish_markers)
