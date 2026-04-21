from app.services.memory_summarizer import RuleBasedMemorySummarizer


def test_rule_based_memory_summarizer_uses_natural_memory_wording() -> None:
    summarizer = RuleBasedMemorySummarizer()

    summary = summarizer.summarize(
        current_summary=None,
        user_message="hoy estoy algo cansado, pero quiero seguir avanzando con el proyecto",
        assistant_message="te entiendo, baja un poco el ritmo",
    )

    assert summary == "The user is tired but still wants to keep making progress with the project."
    assert "The user mentioned:" not in summary
    assert "Assistant replied:" not in summary


def test_rule_based_memory_summarizer_appends_to_existing_summary() -> None:
    summarizer = RuleBasedMemorySummarizer()

    summary = summarizer.summarize(
        current_summary="The user prefers short replies.",
        user_message="hoy estoy algo cansado, pero quiero seguir avanzando con el proyecto",
        assistant_message="te entiendo",
    )

    assert "The user prefers short replies." in summary
    assert "The user is tired but still wants to keep making progress with the project." in summary


def test_rule_based_memory_summarizer_extracts_name_from_message() -> None:
    summarizer = RuleBasedMemorySummarizer()

    summary = summarizer.summarize(
        current_summary=None,
        user_message="hey, me llamo Marcos",
        assistant_message="hola Marcos",
    )

    assert summary == "The user's name is Marcos."


def test_rule_based_memory_summarizer_handles_sensitive_exchange_without_leaking_value() -> None:
    summarizer = RuleBasedMemorySummarizer()

    summary = summarizer.summarize(
        current_summary=None,
        user_message="mi contraseña es 1234",
        assistant_message="mejor no compartas eso",
    )

    assert "1234" not in summary
    assert "sensitive password or credential information" in summary


def test_rule_based_memory_summarizer_handles_empty_exchange() -> None:
    summarizer = RuleBasedMemorySummarizer()

    summary = summarizer.summarize(
        current_summary=None,
        user_message="",
        assistant_message="",
    )

    assert summary == "There was an empty exchange."
