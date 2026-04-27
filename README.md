# Whisper API

API REST para conversión de audio a texto y texto a audio usando **faster-whisper** (CTranslate2).

## Características

- ⚡ **faster-whisper**: Motor de inferencia mucho más rápido que Whisper original
- 🇪🇸 **Optimizado para español**: Usa modelo `large-v3-turbo` con mejor velocidad/precisión
- 🚀 **Cuantización int8**: Acelera el procesamiento en CPU sin perder calidad significativa
- 🔒 **Autenticación por API Keys**: Sistema seguro de autenticación
- 📦 **Sin almacenamiento**: Los audios se procesan en memoria, no se guardan

## Arquitectura

El proyecto está organizado por servicios con la siguiente estructura:

```
app/
├── main.py              # Enrutador principal
├── config/              # Configuraciones del proyecto
├── core/                # Dependencias y excepciones compartidas
└── services/            # Servicios de la API
    ├── health/          # Servicio de health check
    ├── api_keys/        # Servicio de gestión de API Keys
    └── whisper/         # Servicio de conversión de audio
```

Cada servicio contiene:
- `controller/`: Endpoints de la API
- `service/`: Lógica de negocio
- `model/`: DTOs y modelos
- `utils/`: Utilidades y validadores

## Instalación

**Requisito**: Python 3.11, 3.12, 3.13 o 3.14. En macOS puede ser necesario usar `python3` en lugar de `python`.

1. Crear entorno virtual:
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. Instalar dependencias de Python:
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

4. Inicializar la base de datos:
```bash
python scripts/init_db.py
```

## Ejecución

### Opción 1: Usando el script de inicio (recomendado)
El script lee automáticamente `host` y `port` del archivo `.env`:

```bash
python3 run.py
```

### Opción 2: Ejecutar main.py directamente
```bash
python -m app.main
```

### Opción 3: Usando uvicorn directamente
Si prefieres especificar host y port manualmente:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Nota**: Las opciones 1 y 2 usan automáticamente los valores de `HOST` y `PORT` configurados en tu archivo `.env`.

## Docker (recomendado para Dokploy)

Se incluyen estos archivos para despliegue:
- `Dockerfile`
- `.dockerignore`
- `docker-compose.yml`

### Ejecutar local con Docker Compose

```bash
cp .env.docker.example .env
docker compose up --build
```

API disponible en: `http://localhost:8000`

### Despliegue en Dokploy

1. Selecciona el repositorio y usa `Dockerfile` (build desde raíz del proyecto `api-whisper`).
2. Configura variables de entorno (mínimas recomendadas):
   - `HOST=0.0.0.0`
   - `PORT=8000`
   - `DEBUG=false`
   - `WHISPER_MODEL=small` (si tienes poca RAM, usa `base` o `tiny`)
   - `WHISPER_DEVICE=cpu`
   - `WHISPER_COMPUTE_TYPE=int8`
   - `WHISPER_NUM_WORKERS=1`
3. Opcional: agrega `HF_TOKEN` para descargar modelos más rápido.
4. Expón el puerto `8000` en Dokploy.

## Endpoints

### Health
- `GET /health` - Verificar estado de la API

### API Keys
- `POST /api-keys` - Crear nueva API key
- `GET /api-keys` - Listar API keys
- `GET /api-keys/{id}` - Obtener API key
- `POST /api-keys/{id}/activate` - Activar API key
- `POST /api-keys/{id}/deactivate` - Desactivar API key
- `DELETE /api-keys/{id}` - Eliminar API key

### Whisper (requieren API Key)
- `POST /whisper/audio-to-text` - Convertir audio a texto (retorna JSON con el texto)
- `POST /whisper/text-to-audio` - Convertir texto a audio (retorna archivo MP3 directamente, se puede reproducir)

## Autenticación

La API utiliza API Keys para autenticación. Debes incluir el header `X-API-Key` en todas las peticiones a los endpoints protegidos.

### Crear una API Key
```bash
curl -X POST "http://localhost:8000/api-keys" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cliente Producción",
    "description": "API key para cliente en producción",
    "expires_days": 365
  }'
```

### Usar API Key en requests
```bash
curl -X POST "http://localhost:8000/whisper/audio-to-text" \
  -H "X-API-Key: sk_tu_api_key_aqui" \
  -F "audio_file=@audio.wav" \
  -F "language=es" \
  -F "task=transcribe"
```

## Documentación

Una vez ejecutando el servidor, accede a:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Colección de Postman

Se incluye una colección completa de Postman para probar todos los endpoints:

1. **Importar la colección**:
   - Abre Postman
   - Click en "Import"
   - Selecciona `Whisper_API.postman_collection.json`
   - Opcional: Importa también `Whisper_API.postman_environment.json` para las variables de entorno

2. **Configurar variables**:
   - `base_url`: URL base de la API (por defecto: http://127.0.0.1:8000)
   - `api_key`: Tu API Key (se obtiene del endpoint "Crear API Key")
   - `api_key_id`: ID de la API Key (se obtiene al crear una)

3. **Flujo de uso**:
   - Primero ejecuta "Crear API Key" y copia la `key` y `id` de la respuesta
   - Actualiza las variables `api_key` y `api_key_id` en Postman
   - Ahora puedes usar los endpoints de Whisper que requieren autenticación

### Endpoints incluidos en la colección:

- **Health**: Health check
- **API Keys**: Crear, listar, obtener, activar, desactivar, eliminar
- **Whisper**: Audio a texto, Texto a audio

## Configuración de Whisper

### Modelos disponibles
- `tiny`, `base`, `small`, `medium`: Modelos más rápidos pero menos precisos
- `large-v1`, `large-v2`, `large-v3`: Modelos más precisos pero más lentos
- `large-v3-turbo`: **Recomendado para español** - Balance óptimo velocidad/precisión

### Configuración en `.env`
```env
# Modelo recomendado para español
WHISPER_MODEL=large-v3-turbo

# Dispositivo: cpu o cuda (para GPU)
WHISPER_DEVICE=cpu

# Tipo de computación:
# - int8: Más rápido en CPU (recomendado)
# - int8_float16: Balance
# - float16: Más preciso en GPU
WHISPER_COMPUTE_TYPE=int8

# Idioma por defecto (es para español)
WHISPER_LANGUAGE=es
```

### Selección de idioma
- Puedes especificar el idioma en cada request: `language=es` para español
- Usa `language=auto` o `language=None` para detección automática
- Si no especificas, se usa el idioma configurado en `.env`

### Token de Hugging Face (Opcional)

Si ves el warning sobre requests no autenticados a Hugging Face Hub, puedes configurar un token opcional:

1. **Obtener un token**:
   - Ve a https://huggingface.co/settings/tokens
   - Crea un nuevo token (tipo "Read")
   - Copia el token

2. **Configurar en `.env`**:
   ```env
   HF_TOKEN=tu_token_aqui
   ```

**Nota**: El token es opcional. Sin él, la API funciona normalmente pero con límites de descarga más bajos. Con el token, tendrás descargas más rápidas y sin warnings.

### Configuración de TTS (Text-to-Speech)

La API soporta dos proveedores de TTS que puedes configurar en `.env`:

#### Google TTS (gTTS) - Por defecto
- **Gratis** y sin límites
- Calidad básica pero funcional
- Soporta múltiples idiomas
- No requiere API key

```env
TTS_PROVIDER=google
```

#### ElevenLabs - Mejor calidad
- **Mejor calidad de voz** (más natural)
- Requiere API key (tiene límites según plan)
- Soporta múltiples idiomas con modelo multilingüe
- Voces personalizables

```env
TTS_PROVIDER=elevenlabs
ELEVENLABS_API_KEY=tu_api_key_aqui
ELEVENLABS_VOICE_ID=  # Opcional, usa tu primera voz personalizada si está vacío
```

**⚠️ Importante para usuarios gratuitos**:
- Los usuarios del plan gratuito **NO pueden usar voces de la biblioteca** de ElevenLabs
- Debes **crear tu propia voz** en https://elevenlabs.io/app/voice-library
- Una vez creada, copia el `voice_id` y configúralo en `ELEVENLABS_VOICE_ID`
- Si `ELEVENLABS_VOICE_ID` está vacío, el sistema intentará usar tu primera voz personalizada disponible

**Para usuarios con suscripción de pago**:
- Puedes usar cualquier voz de la biblioteca
- Voces recomendadas en español:
  - `nMPrFLO7QElx9wTR0JGo` - Ginyin (masculino, España)
  - `GPzYRfJNEJniCw2WrKzi` - Yinet (femenino, Colombia)
  - `15bJsujCI3tcDWeoZsQP` - Santiago (masculino, México)

Ver todas las voces disponibles en: https://elevenlabs.io/app/voice-library

## Notas

- Los audios NO se guardan en BD, se procesan en memoria
- Las API keys se muestran completas SOLO al crearlas
- En producción, usar HTTPS y configurar CORS específico
- faster-whisper es mucho más rápido que openai-whisper (hasta 4x más rápido)
- El modelo se descarga automáticamente la primera vez que se usa
- Whisper no soporta TTS nativamente, necesitarás otro servicio para text-to-audio
