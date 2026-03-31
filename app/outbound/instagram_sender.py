import requests

from app.core.settings import Settings
from app.models.outbound import OutboundChannelMessage
from app.outbound.result import OutboundSendResult


class InstagramOutboundSender:

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.api_version = settings.instagram_api_version
        self.ig_user_id = settings.instagram_ig_user_id
        self.access_token = settings.instagram_access_token


    def send(self, message: OutboundChannelMessage) -> OutboundSendResult:
        if not self.ig_user_id:
            return OutboundSendResult(
                status = "failed",
                detail = "INSTAGRAM_IG_USER_ID is not configured",
                external_message_id=None,
            )
        
        if not self.access_token:
            return OutboundSendResult(
                status="failed",
                detail = "INSTAGRAM_ACCESS_TOKEN is not configured",
                external_message_id= None,
            )
        
        if not message.user_id:
            return OutboundSendResult(
                status="failed",
                detail="Outbound message is missing recipient user_id.",
                external_message_id=None,
            )

        if not message.message_text.strip():
            return OutboundSendResult(
                status="failed",
                detail="Outbound message text is empty.",
                external_message_id=None,
            )
        
        url = f"https://graph.instagram.com/{self.api_version}/{self.ig_user_id}/messages"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "recipient": {
                "id": message.user_id,
            },
            "message": {
                "text": message.message_text,
            }
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()

        except requests.RequestException as exc:
            return OutboundSendResult(
                status="failed",
                detail=f"Instagram outbound request failed: {exc}",
                external_message_id=None,
            )
        
        try:
            data = response.json()
        except ValueError:
            return OutboundSendResult(
                status="sent",
                detail="Instagram outbound message sent successfully, but response JSON could not be parsed.",
                external_message_id=None,
            )
        
        external_message_id = data.get("message_id")

        return OutboundSendResult(
            status="sent",
            detail="Instagram outbound message sent successfully",
            external_message_id=external_message_id
        )