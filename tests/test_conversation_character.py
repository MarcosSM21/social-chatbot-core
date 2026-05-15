from app.models.conversation_character import ConversationCharacter


def test_loads_support_concierge_extended_fields() -> None:
    character = ConversationCharacter.from_json_file("characters/support_concierge.json")

    assert character.character_id == "support_concierge"
    assert character.display_name == "Maya"
    assert character.inner_world
    assert character.motivations
    assert character.aspirations
    assert character.contradictions
    assert character.worldview
    assert character.relationship_dynamic
    assert character.conversation_habits
    assert character.do_not_perform


def test_loads_sales_qualifier_extended_fields() -> None:
    character = ConversationCharacter.from_json_file("characters/sales_qualifier.json")

    assert character.character_id == "sales_qualifier"
    assert character.display_name == "Nora"
    assert character.inner_world
    assert character.motivations
    assert character.aspirations
    assert character.contradictions
    assert character.worldview
    assert character.relationship_dynamic
    assert character.conversation_habits
    assert character.do_not_perform
