# Production Control Checklist

Esta guía sirve para activar el bot de Instagram de forma controlada.

Objetivo: evitar que el bot responda a usuarios no deseados, que los endpoints internos queden expuestos o que una configuración insegura pase desapercibida.

## Estado Recomendado Para Pruebas Reales

Antes de activar respuestas automáticas, empieza en modo escucha:

```env
BOT_ENABLED=false
```

Con este modo:

- llegan DMs reales
- se guardan raw payloads
- se guardan trazas operativas
- no se llama al LLM
- no se envía respuesta a Instagram

Comprueba eventos con:

```bash
curl \
  -H "X-Internal-API-Key: <INTERNAL_API_KEY>" \
  "http://localhost:8000/internal/operations/events?platform=instagram&limit=5"
```

Comprueba resumen con:

```bash
curl \
  -H "X-Internal-API-Key: <INTERNAL_API_KEY>" \
  "http://localhost:8000/internal/operations/summary?platform=instagram"
```

## Checklist Antes De `BOT_ENABLED=true`

### 1. API interna protegida

Configura una clave interna no trivial:

```env
INTERNAL_API_KEY=<clave-larga-y-no-publica>
```

Todos los endpoints internos deben usarse con:

```http
X-Internal-API-Key: <INTERNAL_API_KEY>
```

Endpoints internos protegidos:

```text
POST   /internal/messages
GET    /internal/memory/{platform}
GET    /internal/memory/{platform}/{external_user_id}
DELETE /internal/memory/{platform}/{external_user_id}
DELETE /internal/memory/empty
GET    /internal/operations/events
GET    /internal/operations/summary
```



### 2. Webhook de Instagram configurado

La callback URL debe ser:

```text
https://<host-publico>/providers/instagram/webhook/messages
```

El mismo path sirve para:

```text
GET  verificacion
POST recepcion de mensajes
```

Comprueba que Meta está suscrito al campo:

```text
messages
```

### 3. Firma de webhook activa

Debe existir:

```env
INSTAGRAM_APP_SECRET=...
```

Si falta, el webhook debe fallar con error de configuración.

### 4. Token y cuenta correctos

Comprueba:

```env
INSTAGRAM_IG_USER_ID=...
INSTAGRAM_ACCESS_TOKEN=...
INSTAGRAM_API_VERSION=v25.0
```

Y confirma que:

- el token corresponde a la cuenta profesional correcta
- la cuenta está suscrita a `messages`
- la app tiene permisos necesarios
- el token no está caducado
- si el token se ha compartido accidentalmente, debe rotarse

### 5. Modo de respuesta controlado

Para responder solo a usuarios concretos:

```env
INSTAGRAM_ALLOWED_USER_IDS=<user_id_1>,<user_id_2>
```

Si está vacío:

```env
INSTAGRAM_ALLOWED_USER_IDS=
```

el bot puede responder a cualquier usuario que escriba, siempre que `BOT_ENABLED=true`.

Recomendación para pruebas iniciales:

```env
INSTAGRAM_ALLOWED_USER_IDS=<id-de-tu-cuenta-secundaria>
```

### 6. Anti-spam básico activo

Configura un cooldown razonable:

```env
INSTAGRAM_REPLY_COOLDOWN_SECONDS=10
```

Si está en `0`, queda desactivado:

```env
INSTAGRAM_REPLY_COOLDOWN_SECONDS=0
```

Recomendación inicial:

```env
INSTAGRAM_REPLY_COOLDOWN_SECONDS=10
```

### 7. Backend de memoria elegido

Modo simple JSON:

```env
MEMORY_STORAGE_BACKEND=json
```

Modo recomendado para uso más serio:

```env
MEMORY_STORAGE_BACKEND=sqlite
SQLITE_DATABASE_PATH=data/social_chatbot.sqlite3
```

Si vienes de JSON y quieres migrar memorias:

```bash
.venv/bin/python scripts/migrate_user_memories_to_sqlite.py --dry-run
.venv/bin/python scripts/migrate_user_memories_to_sqlite.py
```

### 8. Provider LLM claro

Para mock:

```env
GENERATION_PROVIDER=mock
```

Para Ollama:

```env
GENERATION_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3
OLLAMA_TIMEOUT_SECONDS=60
```

Antes de usar Ollama en real:

- comprueba que Ollama está levantado
- comprueba que el modelo responde
- revisa si `ENABLE_PROVIDER_FALLBACK=true` te conviene o puede ocultar fallos

### 9. Personaje correcto

Comprueba:

```env
CHARACTER_FILE=characters/quiet_close_friend.json
```

o el personaje que quieras usar.

Antes de responder a usuarios reales, ejecuta evaluación local si has cambiado personaje o prompt.

### 10. Privacidad y datos

Antes de abrir a más usuarios:

- revisa `data/provider_raw_payloads.json`
- revisa `data/external_traces.json`
- revisa `data/user_memories.json` o SQLite
- no compartas estos archivos si contienen datos reales
- considera limpiar payloads antiguos si ya no son necesarios
- recuerda que raw payloads pueden contener identificadores reales

## Activación Recomendada

### Paso A: escucha sin responder

```env
BOT_ENABLED=false
INSTAGRAM_ALLOWED_USER_IDS=<id-de-tu-cuenta-secundaria>
INSTAGRAM_REPLY_COOLDOWN_SECONDS=10
```

Reinicia FastAPI.

Envía un DM real.

Comprueba:

```bash
curl \
  -H "X-Internal-API-Key: <INTERNAL_API_KEY>" \
  "http://localhost:8000/internal/operations/events?platform=instagram&limit=5"
```

Debe aparecer:

```json
{
  "operational_status": "bot_disabled",
  "outbound_status": "not_sent"
}
```

### Paso B: responder solo a usuario permitido

```env
BOT_ENABLED=true
INSTAGRAM_ALLOWED_USER_IDS=<id-de-tu-cuenta-secundaria>
INSTAGRAM_REPLY_COOLDOWN_SECONDS=10
```

Reinicia FastAPI.

Envía otro DM real.

Debe aparecer:

```json
{
  "inbound_status": "processed",
  "outbound_status": "sent",
  "operational_status": "ok"
}
```

### Paso C: probar usuario no permitido

Envía DM desde otra cuenta no incluida en `INSTAGRAM_ALLOWED_USER_IDS`.

Debe aparecer:

```json
{
  "inbound_status": "captured",
  "outbound_status": "not_sent",
  "operational_status": "user_not_allowed"
}
```

### Paso D: probar anti-spam

Envía varios mensajes seguidos desde el mismo usuario permitido.

Alguno debería aparecer como:

```json
{
  "inbound_status": "captured",
  "outbound_status": "not_sent",
  "operational_status": "rate_limited"
}
```

## Señales De Que Se Puede Avanzar

Puedes considerar que el bot está en modo producción controlada si:

- el webhook recibe DMs reales
- `BOT_ENABLED=false` captura sin responder
- `BOT_ENABLED=true` responde al usuario permitido
- usuarios fuera de allowlist no reciben respuesta
- el cooldown evita ráfagas
- los endpoints internos requieren API key
- puedes revisar últimos eventos con `/internal/operations/events`
- puedes revisar resumen con `/internal/operations/summary`
- no hay fallos repetidos de LLM ni de envío a Instagram

## Señales De Que NO Conviene Abrir A Más Usuarios

No abras más el bot si:

- hay muchos `processing_failed`
- hay muchos `outbound_failed`
- responde fuera de personaje
- guarda memoria rara o sensible
- no sabes qué usuario está recibiendo respuestas
- `INSTAGRAM_ALLOWED_USER_IDS` está vacío por accidente
- `INTERNAL_API_KEY` sigue con el valor dev
- el token de Instagram se ha compartido o expuesto