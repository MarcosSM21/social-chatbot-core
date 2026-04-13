from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ExternalTraceRecord:
    platform: str
    external_conversation_id: str
    external_user_id: str
    internal_session_id: str | None
    incoming_message_text: str | None
    outgoing_message_text: str | None
    inbound_status: str
    outbound_status: str | None
    detail: str
    provider_message_id: str | None = None
    outbound_message_id: str | None = None
    memory_loaded: bool | None = None
    memory_updated: bool | None = None
    memory_profile_status: str | None = None
    memory_profile_detail: str | None = None
    memory_profile_matched_rule: str | None = None
    memory_summary_status: str | None = None
    memory_summary_detail: str | None = None
    memory_summary_matched_rule: str | None = None
    style_preset: str | None = None
    style_snapshot: dict[str, Any] | None = None
    safety_policy_active: bool | None = None
    safety_snapshot: dict[str, Any] | None = None
    safety_validation_status: str | None = None
    safety_validation_detail: str | None = None
    safety_matched_rule: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ExternalTraceRecord":
        return cls(
            platform=data["platform"],
            external_conversation_id=data["external_conversation_id"],
            external_user_id=data["external_user_id"],
            internal_session_id=data.get("internal_session_id"),
            incoming_message_text=data.get("incoming_message_text"),
            outgoing_message_text=data.get("outgoing_message_text"),
            inbound_status=data["inbound_status"],
            outbound_status=data.get("outbound_status"),
            detail=data["detail"],
            provider_message_id=data.get("provider_message_id"),
            outbound_message_id=data.get("outbound_message_id"),
            memory_loaded=data.get("memory_loaded"),
            memory_updated =data.get("memory_updated"),
            memory_profile_status=data.get("memory_profile_status"),
            memory_profile_detail=data.get("memory_profile_detail"),
            memory_profile_matched_rule=data.get("memory_profile_matched_rule"),
            memory_summary_status=data.get("memory_summary_status"),
            memory_summary_detail=data.get("memory_summary_detail"),
            memory_summary_matched_rule=data.get("memory_summary_matched_rule"),
            style_preset=data.get("style_preset"),
            style_snapshot=data.get("style_snapshot"),
            safety_policy_active= data.get("safety_policy_active"),
            safety_snapshot=data.get("safety_snapshot"),
            safety_validation_status=data.get("safety_validation_status"),
            safety_validation_detail=data.get("safety_validation_detail"),
            safety_matched_rule=data.get("safety_matched_rule"),
        )