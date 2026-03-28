from app.channels.provider_parser_result import (
    InstagramParsedEvent,
    ProviderPayloadParseResult,
)
from app.models.provider_payloads import InstagramWebhookPayload

class InstagramPayloadParser:
    """Extracts text-based DM events from the real Instagram webhook payload."""

    def parse(self, payload: InstagramWebhookPayload) -> ProviderPayloadParseResult:
        if not payload.object.strip():
            raise ValueError("Instagram payload is missing object.")

        if not payload.entry:
            raise ValueError("Instagram payload contains no entry items.")

        parsed_events: list[InstagramParsedEvent] = []

        for entry in payload.entry:
            entry_has_events = bool(entry.messaging or entry.changes)
            if not entry_has_events:
                parsed_events.append(
                    InstagramParsedEvent(
                        status="ignored",
                        detail="Entry contains no messaging or change events.",
                        external_conversation_id=None,
                        external_user_id=None,
                        incoming_message_text=None,
                    )
                )
                continue

            for event in entry.messaging:
                parsed_events.append(
                    self._parse_message_event(
                        sender_id=event.sender.id.strip(),
                        recipient_id=event.recipient.id.strip(),
                        message=event.message,
                        timestamp=event.timestamp,
                        source="messaging",
                    )
                )

            for change in entry.changes:
                if change.field != "messages":
                    parsed_events.append(
                        InstagramParsedEvent(
                            status="ignored",
                            detail=f"Change field '{change.field}' is not supported.",
                            external_conversation_id=None,
                            external_user_id=None,
                            incoming_message_text=None,
                        )
                    )
                    continue

                if change.value is None:
                    parsed_events.append(
                        InstagramParsedEvent(
                            status="ignored",
                            detail="Change event contains no value payload.",
                            external_conversation_id=None,
                            external_user_id=None,
                            incoming_message_text=None,
                        )
                    )
                    continue

                sender_id = change.value.sender.id.strip() if change.value.sender is not None else ""
                recipient_id = change.value.recipient.id.strip() if change.value.recipient is not None else ""

                parsed_events.append(
                    self._parse_message_event(
                        sender_id=sender_id,
                        recipient_id=recipient_id,
                        message=change.value.message,
                        timestamp=change.value.timestamp,
                        source="changes",
                    )
                )

        captured_count = sum(1 for event in parsed_events if event.status == "captured")
        ignored_count = len(parsed_events) - captured_count

        if captured_count == 0:
            return ProviderPayloadParseResult(
                status="ignored",
                detail=f"No supported text-based DM events found. Ignored {ignored_count} event(s).",
                events=parsed_events,
            )

        return ProviderPayloadParseResult(
            status="captured",
            detail=f"Captured {captured_count} text message(s); ignored {ignored_count} event(s).",
            events=parsed_events,
        )

    def _parse_message_event(
        self,
        sender_id: str,
        recipient_id: str,
        message,
        timestamp: int | str | None,
        source: str,
    ) -> InstagramParsedEvent:
        if not sender_id or not recipient_id:
            return InstagramParsedEvent(
                status="ignored",
                detail=f"{source.capitalize()} event is missing sender or recipient identifiers.",
                external_conversation_id=sender_id or None,
                external_user_id=sender_id or None,
                incoming_message_text=None,
                timestamp=self._normalize_timestamp(timestamp),
            )

        if message is None:
            return InstagramParsedEvent(
                status="ignored",
                detail=f"{source.capitalize()} event contains no message payload.",
                external_conversation_id=sender_id,
                external_user_id=sender_id,
                incoming_message_text=None,
                timestamp=self._normalize_timestamp(timestamp),
            )

        if message.is_echo:
            return InstagramParsedEvent(
                status="ignored",
                detail="Echo message ignored.",
                external_conversation_id=sender_id,
                external_user_id=sender_id,
                incoming_message_text=(message.text or "").strip() or None,
                provider_message_id=message.mid,
                timestamp=self._normalize_timestamp(timestamp),
            )

        message_text = (message.text or "").strip()
        if not message_text:
            return InstagramParsedEvent(
                status="ignored",
                detail=f"{source.capitalize()} event does not contain a usable text message.",
                external_conversation_id=sender_id,
                external_user_id=sender_id,
                incoming_message_text=None,
                provider_message_id=message.mid,
                timestamp=self._normalize_timestamp(timestamp),
            )

        return InstagramParsedEvent(
            status="captured",
            detail=f"Instagram text message captured from {source} payload.",
            external_conversation_id=sender_id,
            external_user_id=sender_id,
            incoming_message_text=message_text,
            provider_message_id=message.mid,
            timestamp=self._normalize_timestamp(timestamp),
        )

    def _normalize_timestamp(self, timestamp: int | str | None) -> int | None:
        if timestamp is None:
            return None
        if isinstance(timestamp, int):
            return timestamp
        if isinstance(timestamp, str) and timestamp.isdigit():
            return int(timestamp)
        return None
