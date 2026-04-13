import hashlib
import hmac
import json

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app.api.schemas import (
    MessageRequest,
    MessageResponse,
    HealthResponse,
    InfoResponse,
    WebhookMessageRequest,
    WebhookEventResponse,
    InstagramWebhookPayloadRequest,
)

from app.channels.http_channel_result import HttpChannelResult
from app.channels.instagram_payload_parser import InstagramPayloadParser
from app.channels.provider_parser_result import ProviderPayloadParseResult
from app.models.provider_payloads import InstagramWebhookPayload


from app.core.settings import Settings
from app.models.external import ExternalMessageEvent
from app.core.container import build_http_channel_adapter, build_platform_inbound_service
from app.models.platform_payload import PlatformWebhookPayload
from app.providers.exceptions import GenerationProviderError
from app.storage.external_trace_repository import ExternalTraceRepository
from app.models.external_trace import ExternalTraceRecord
from app.models.provider_raw_payload import ProviderRawPayloadRecord
from app.storage.provider_raw_payload_repository import ProviderRawPayloadRepository
from app.outbound.instagram_sender import InstagramOutboundSender
from app.outbound.result import OutboundSendResult





app = FastAPI(
    title="social-chatbot-core API",
    version="0.1.0",
    description="Interanl API para el chatbot social core project"
)

settings = Settings.from_env()


###### RUTAS AUXILIARES ##########
@app.get("/")
def root() -> dict:
    return {
        "message": "social-chatbot-core API is running",
        "docs_url": "/docs",
        "health_url": "/health",
        "info_url": "/info",
        "privacy_policy_url": "/privacy-policy",
        "internal_messages_url": "/internal/messages",
        "generic_webhook_verify_url": "/webhooks/verify",
        "generic_webhook_messages_url": "/webhooks/messages",
        "instagram_webhook_verify_url": "/providers/instagram/webhook/verify",
        "instagram_webhook_messages_url": "/providers/instagram/webhook/messages",
    }

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")

@app.get("/info", response_model=InfoResponse)
def info() -> InfoResponse:
    return InfoResponse(
        service_name="social-chatbot-core",
        version="0.1.0",
        enviroment=settings.app_env,
        llm_provider=settings.llm_provider
    )
@app.get("/privacy-policy", response_class=HTMLResponse)
def privacy_policy() -> HTMLResponse:
    html = """
    <!DOCTYPE html>
    <html lang="es">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Politica de Privacidad | social-chatbot-core</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            background: #f7f7f5;
            color: #1f2937;
            margin: 0;
            padding: 40px 20px;
          }
          main {
            max-width: 760px;
            margin: 0 auto;
            background: #ffffff;
            padding: 32px;
            border-radius: 16px;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
          }
          h1, h2 {
            color: #111827;
          }
          p, li {
            line-height: 1.6;
          }
          ul {
            padding-left: 20px;
          }
          .note {
            margin-top: 24px;
            padding: 16px;
            background: #fef3c7;
            border-radius: 12px;
          }
        </style>
      </head>
      <body>
        <main>
          <h1>Politica de Privacidad</h1>
          <p>
            Esta es una pagina provisional de politica de privacidad para
            <strong>social-chatbot-core</strong>.
          </p>

          <h2>Datos que pueden tratarse</h2>
          <ul>
            <li>Mensajes enviados por usuarios a traves de canales conectados.</li>
            <li>Identificadores tecnicos de conversacion y plataforma.</li>
            <li>Registros tecnicos necesarios para depuracion y trazabilidad.</li>
          </ul>

          <h2>Finalidad</h2>
          <p>
            Los datos se utilizan exclusivamente para pruebas tecnicas,
            integraciones de mensajeria, procesamiento conversacional y
            seguimiento operativo del sistema.
          </p>

          <h2>Conservacion</h2>
          <p>
            Durante esta fase de desarrollo, algunos datos pueden almacenarse
            temporalmente en registros locales con fines de prueba.
          </p>

          <h2>Contacto</h2>
          <p>
            Si necesitas una version formal o definitiva de esta politica,
            sustituye este contenido por la informacion legal real del proyecto
            antes de usarlo en produccion.
          </p>

          <div class="note">
            Este documento es un mockup tecnico para desarrollo y configuracion
            inicial de integraciones.
          </div>
        </main>
      </body>
    </html>
    """
    return HTMLResponse(content=html)

###########################################

########### MENSAJES ########################

@app.post("/internal/messages", response_model=MessageResponse)
def create_internal_message(request: MessageRequest) -> MessageResponse:
    
    event = ExternalMessageEvent(
        platform="api",
        conversation_id=request.session_id,
        user_id="api-user",
        message_text=request.message,
        channel_metadata={
            "source": "internal_api"
        }
    )
    
    http_channel_adapter = build_http_channel_adapter(settings)

    

    try:
        channel_result = http_channel_adapter.process_event(event)
    except GenerationProviderError as exc:
        raise HTTPException(status_code=503, detail=f"Generation provider error: {exc}") from exc

    return MessageResponse(
        user_message=channel_result.turn.user_message.content,
        assistant_message=channel_result.turn.assistant_message.content,
        session_id=channel_result.turn.session_id
    )


@app.post("/webhooks/messages")
def receive_webhook_message(request: WebhookMessageRequest) -> MessageResponse | WebhookEventResponse:
    
    inbound_service = build_platform_inbound_service(settings)

    payload = PlatformWebhookPayload(
        platform=request.platform,
        event_type=request.event_type,
        conversation_id=request.conversation_id,
        user_id=request.user_id,
        message_text=request.message_text,
        message_id=request.message_id,
        payload_id=request.payload_id,
        raw_payload=request.channel_metadata,
    )

    

    try:
        inbound_result = inbound_service.process_payload(payload)

        if inbound_result.status == "ignored":
            return WebhookEventResponse(
                status="ignored",
                detail=inbound_result.detail
            )
        if inbound_result.channel_result is None:
            return HTTPException(
                status_code=500,
                detail = "Parser returned no event for a processable payload"
            )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {exc}") from exc
    except GenerationProviderError as exc:
        raise HTTPException(status_code=503, detail=f"Generation provider error: {exc}") from exc

    turn = inbound_result.channel_result.turn

    return MessageResponse(
        session_id=turn.session_id,
        user_message=turn.user_message.content,
        assistant_message=turn.assistant_message.content
    )



###################### INSTAGRAM RECIBE MENSAJE EN DM #######################################

@app.post("/providers/instagram/webhook/messages", response_model=WebhookEventResponse)
async def receive_instagram_webhook_message(request: Request) -> WebhookEventResponse:
    raw_body = await request.body()
    signature_header = request.headers.get("X-Hub-Signature-256")

    _validate_instagram_webhook_signature(raw_body, signature_header)

    raw_payload = _decode_instagram_webhook_payload(raw_body)
    provider_payload_request = _parse_instagram_webhook_request(raw_body)
    provider_payload = InstagramWebhookPayload.from_dict(
        provider_payload_request.model_dump(mode="json")
    )

    _store_instagram_raw_payload(raw_payload)
    provider_parser_result, external_events = _build_external_events(provider_payload)
    trace_repository = ExternalTraceRepository()

    if external_events:
        external_event = external_events[0]

        if trace_repository.has_processed_provider_message(external_event.message_id):
            return WebhookEventResponse(
                status="ignored",
                detail="Duplicate provider message ignored.",
            )

        channel_result, send_result = _process_and_send_external_event(external_event)
        _save_processed_trace(trace_repository, external_event, channel_result, send_result)


    response_status = "accepted" if provider_parser_result.status == "captured" else "ignored"
    return WebhookEventResponse(
        status=response_status,
        detail=provider_parser_result.detail,
    )

### VERIFICACION INSTAGRAM ###
@app.get("/providers/instagram/webhook/messages")
def verify_instagram_webhook_messages(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
):
    return execute_webhook_verification(
        mode=hub_mode,
        token=hub_token,
        challenge=hub_challenge,
    )


@app.get("/webhooks/verify")
def verify_generic_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
):
    return execute_webhook_verification(mode=hub_mode, token=hub_token, challenge=hub_challenge)


#==============FUNCIONES_AUXILIARES=====================

def execute_webhook_verification(mode: str, token: str, challenge: str):
    if mode != "subscribe":
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    if token != settings.webhook_verify_token:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    # IMPORTANTE: Retornamos Response para enviar texto plano, no JSON
    return Response(content=challenge, media_type="text/plain")


def _parse_instagram_webhook_request(raw_body: bytes) -> InstagramWebhookPayloadRequest:
    try:
        return InstagramWebhookPayloadRequest.model_validate_json(raw_body)
    except ValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid Instagram webhook payload",
        ) from exc


def _decode_instagram_webhook_payload(raw_body: bytes) -> dict:
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=400,
            detail="Instagram webhook payload is not valid JSON",
        ) from exc

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=400,
            detail="Instagram webhook payload must be a JSON object",
        )

    return payload


def _store_instagram_raw_payload(raw_payload: dict) -> None:
    raw_payload_repository = ProviderRawPayloadRepository()
    raw_payload_repository.save_record(
        ProviderRawPayloadRecord(
            provider="instagram",
            endpoint="/providers/instagram/webhook/messages",
            payload=raw_payload,
        )
    )


def _build_external_events(
    provider_payload: InstagramWebhookPayload,
) -> tuple[ProviderPayloadParseResult, list[ExternalMessageEvent]]:
    parser = InstagramPayloadParser()
    provider_parser_result = parser.parse(provider_payload)

    external_events: list[ExternalMessageEvent] = []
    for parsed_event in provider_parser_result.events:
        external_event = parsed_event.to_external_message_event()
        if external_event is not None:
            external_events.append(external_event)

    return provider_parser_result, external_events


def _process_and_send_external_event(
    external_event: ExternalMessageEvent,
) -> tuple[HttpChannelResult, OutboundSendResult]:
    channel_adapter = build_http_channel_adapter(settings)
    channel_result = channel_adapter.process_event(external_event)

    instagram_sender = InstagramOutboundSender(settings)
    send_result = instagram_sender.send(channel_result.outbound_message)

    return channel_result, send_result


def _save_processed_trace(
    trace_repository: ExternalTraceRepository,
    external_event: ExternalMessageEvent,
    channel_result: HttpChannelResult,
    send_result: OutboundSendResult,
) -> None:
    
    turn_metadata = channel_result.turn.session_metadata or {}

    trace_repository.save_records(
        ExternalTraceRecord(
            platform="instagram",
            external_conversation_id=external_event.conversation_id,
            external_user_id=external_event.user_id,
            internal_session_id=channel_result.turn.session_id,
            incoming_message_text=external_event.message_text,
            outgoing_message_text=channel_result.outbound_message.message_text,
            inbound_status="processed",
            outbound_status=send_result.status,
            detail=f"Inbound Instagram message processed by internal core. Outbound result: {send_result.detail}",
            provider_message_id=external_event.message_id,
            outbound_message_id=send_result.external_message_id,
            memory_loaded=turn_metadata.get("memory_loaded"),
            memory_updated=turn_metadata.get("memory_updated"),
            memory_profile_status=turn_metadata.get("memory_profile_status"),
            memory_profile_detail=turn_metadata.get("memory_profile_detail"),
            memory_profile_matched_rule=turn_metadata.get("memory_profile_matched_rule"),
            memory_summary_status=turn_metadata.get("memory_summary_status"),
            memory_summary_detail=turn_metadata.get("memory_summary_detail"),
            memory_summary_matched_rule=turn_metadata.get("memory_summary_matched_rule"),
            style_preset=turn_metadata.get("style_preset"),
            style_snapshot=turn_metadata.get("style_snapshot"),
            safety_policy_active=turn_metadata.get("safety_policy_active"),
            safety_snapshot=turn_metadata.get("safety_snapshot"),
            safety_validation_status=turn_metadata.get("safety_validation_status"),
            safety_validation_detail=turn_metadata.get("safety_validation_detail"),
            safety_matched_rule=turn_metadata.get("safety_matched_rule"),

        )
    )


def _validate_instagram_webhook_signature(raw_body: bytes, signature_header: str | None) -> None:
    if not settings.instagram_app_secret:
        raise HTTPException(
            status_code=500,
            detail="INSTAGRAM_APP_SECRET is not configured",
        )

    if not signature_header:
        raise HTTPException(status_code=403, detail="Missing webhook signature")

    expected_signature = "sha256=" + hmac.new(
        settings.instagram_app_secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature_header.strip()):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")
