# Instagram DM Debugging Guide

Esta guía sirve para diagnosticar problemas reales del flujo de DMs de Instagram.

Objetivo: entender rápidamente si el problema está en Meta/Instagram, webhook, parser, bot core, memoria, LLM o envío saliente.

## Flujo Real Esperado

```text
Usuario envía DM en Instagram
   -> Meta envía POST al webhook
   -> FastAPI recibe /providers/instagram/webhook/messages
   -> se valida firma X-Hub-Signature-256
   -> se guarda raw payload en data/provider_raw_payloads.json
   -> se parsea payload de Instagram
   -> se crea ExternalMessageEvent
   -> se comprueba duplicado por provider_message_id
   -> si BOT_ENABLED=false:
        se guarda traza bot_disabled
        no se genera respuesta
        no se envía nada
   -> si BOT_ENABLED=true:
        se procesa con el core conversacional
        se genera respuesta
        se envía por InstagramOutboundSender
        se guarda traza procesada
```

## Comprobación rápida

### 1. API viva

```bash
curl http://localhost:8000/health
```

Respuesta esperada:

```json
{"status":"ok"}
```

### 2. Webhook correcto en Meta

La callback URL debe apuntar al endpoint de Instagram:

```text
https://<host-publico>/providers/instagram/webhook/messages
```

El mismo path sirve para verificación `GET` y recepción real `POST`:

```text
GET  /providers/instagram/webhook/messages
POST /providers/instagram/webhook/messages
```

### 3. Ver últimos eventos operativos

```bash
curl "http://localhost:8000/internal/operations/events?platform=instagram&limit=5"
```

### 4. Ver resumen operativo

```bash
curl "http://localhost:8000/internal/operations/summary?platform=instagram"
```

## Archivos útiles

Payloads crudos recibidos desde Meta:

```text
data/provider_raw_payloads.json
```

Trazas operativas del flujo:

```text
data/external_traces.json
```

Memoria de usuarios:

```text
data/user_memories.json
```

O SQLite si está activado:

```env
MEMORY_STORAGE_BACKEND=sqlite
SQLITE_DATABASE_PATH=data/social_chatbot.sqlite3
```

## Interpretar estados

### `inbound_status="ignored"`

El webhook llegó, pero no contenía un DM de texto procesable.

Puede ocurrir con:

- eventos vacíos
- mensajes sin `text`
- echo messages
- eventos no soportados
- payloads de prueba de Meta sin `messaging`

Ejemplo:

```json
{
  "inbound_status": "ignored",
  "detail": "Entry contains no messaging events."
}
```

### `inbound_status="captured"`

El mensaje fue capturado como DM válido, pero no se procesó con el core.

Caso principal:

```json
{
  "inbound_status": "captured",
  "outbound_status": "not_sent",
  "operational_status": "bot_disabled"
}
```

Significa que el bot está en modo escucha:

```env
BOT_ENABLED=false
```

### `inbound_status="processed"`

El mensaje pasó por el core conversacional.

Caso sano:

```json
{
  "inbound_status": "processed",
  "outbound_status": "sent",
  "operational_status": "ok"
}
```

### `inbound_status="processing_failed"`

El mensaje llegó, pero falló antes de poder enviar respuesta.

Normalmente apunta a:

- proveedor LLM caído
- Ollama no disponible
- timeout del modelo
- error interno del core conversacional

Ejemplo:

```json
{
  "inbound_status": "processing_failed",
  "outbound_status": "not_sent",
  "operational_status": "processing_failed",
  "operational_error_type": "generation_provider_error"
}
```

### `operational_status="outbound_failed"`

El core generó respuesta, pero falló el envío a Instagram.

Puede apuntar a:

- token inválido
- permisos insuficientes
- recipient incorrecto
- error de Graph API
- timeout saliente

Ejemplo:

```json
{
  "inbound_status": "processed",
  "outbound_status": "failed",
  "operational_status": "outbound_failed",
  "operational_error_type": "instagram_outbound_failed"
}
```

## Checklist: no llega el DM

1. Comprueba que FastAPI está vivo.
2. Comprueba que el túnel público sigue vivo.
3. Comprueba que la URL de Meta apunta al túnel actual.
4. Comprueba que la callback URL es `/providers/instagram/webhook/messages`.
5. Comprueba que la app está suscrita al campo `messages`.
6. Comprueba `GET /{ig_user_id}/subscribed_apps`.
7. Comprueba que la app está en producción o que la cuenta emisora es válida para desarrollo.
8. Comprueba que la cuenta profesional de Instagram es la conectada al token.
9. Mira si aparece un `POST` en la terminal de FastAPI.
10. Mira si se añadió algo en `data/provider_raw_payloads.json`.

## Checklist: llega pero no responde

1. Mira `data/external_traces.json`.
2. Ejecuta `GET /internal/operations/events?platform=instagram&limit=5`.
3. Si `operational_status="bot_disabled"`, activa `BOT_ENABLED=true` y reinicia FastAPI.
4. Si `inbound_status="ignored"`, el payload no tenía DM de texto soportado.
5. Si `inbound_status="processing_failed"`, revisa Ollama o el proveedor LLM.
6. Si `operational_status="outbound_failed"`, revisa token, permisos y envío a Instagram.
7. Si no hay traza pero sí raw payload, revisa parser o flujo de firma.
8. Si hay duplicado, revisa `provider_message_id`.

## Checklist: responde raro

1. Mira la última traza operativa.
2. Revisa `memory_loaded`.
3. Revisa `memory_updated`.
4. Revisa `style_preset`.
5. Revisa `safety_validation_status`.
6. Revisa memoria del usuario con `GET /internal/memory/instagram/<external_user_id>`.
7. Revisa qué personaje está activo en `CHARACTER_FILE`.
8. Ejecuta evaluación local con el mismo personaje.
9. Ajusta el character file antes de tocar arquitectura.

## Comandos útiles

Últimos eventos:

```bash
curl "http://localhost:8000/internal/operations/events?platform=instagram&limit=5"
```

Resumen operativo:

```bash
curl "http://localhost:8000/internal/operations/summary?platform=instagram"
```

Ver memoria de Instagram:

```bash
curl http://localhost:8000/internal/memory/instagram
```

Ver memoria de un usuario:

```bash
curl http://localhost:8000/internal/memory/instagram/<external_user_id>
```

Borrar memoria de un usuario:

```bash
curl -X DELETE http://localhost:8000/internal/memory/instagram/<external_user_id>
```

Borrar memorias vacías:

```bash
curl -X DELETE http://localhost:8000/internal/memory/empty
```

## Modo escucha recomendado

Para probar cambios de personaje, memoria o modelo con Instagram real:

1. Configura:

```env
BOT_ENABLED=false
```

2. Reinicia FastAPI.
3. Envía DMs reales.
4. Revisa eventos y payloads.
5. Si todo llega bien, configura:

```env
BOT_ENABLED=true
```

6. Reinicia FastAPI.
7. Prueba respuestas reales con una cuenta controlada.

