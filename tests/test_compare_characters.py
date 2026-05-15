from scripts.compare_characters import run_character_case, reset_runtime_storage


def test_compare_characters_uses_requested_character_file() -> None:
    reset_runtime_storage()

    result = run_character_case(
        character_file="characters/support_concierge.json",
        message="holaa",
        provider="mock",
        session_id="test-session",
        external_user_id="test-user",
    )

    assert result["character_id"] == "support_concierge"
    assert result["character_name"] == "Maya"
    assert result["user_message"] == "holaa"
    assert result["assistant_message"]


def test_compare_characters_can_switch_between_characters() -> None:
    reset_runtime_storage()

    support_result = run_character_case(
        character_file="characters/support_concierge.json",
        message="holaa",
        provider="mock",
        session_id="test-session-support",
        external_user_id="test-user-support",
    )
    sales_result = run_character_case(
        character_file="characters/sales_qualifier.json",
        message="holaa",
        provider="mock",
        session_id="test-session-sales",
        external_user_id="test-user-sales",
    )

    assert support_result["character_id"] == "support_concierge"
    assert sales_result["character_id"] == "sales_qualifier"
    assert support_result["character_name"] == "Maya"
    assert sales_result["character_name"] == "Nora"
