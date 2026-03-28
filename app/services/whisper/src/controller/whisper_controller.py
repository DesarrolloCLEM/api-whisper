from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi.responses import Response
from app.services.whisper.src.service import WhisperService
from app.services.whisper.src.model import (
    AudioToTextRequest,
    AudioToTextResponse,
    TextToAudioRequest
)
from app.core.dependencies import get_api_key_user
from typing import Optional
import logging

router = APIRouter(prefix="/whisper", tags=["Whisper"])

service = WhisperService()
logger = logging.getLogger(__name__)


@router.post("/audio-to-text", response_model=AudioToTextResponse)
async def audio_to_text(
    audio_file: UploadFile = File(..., description="Archivo de audio"),
    language: Optional[str] = Form(None, description="Código de idioma (ej: 'es', 'en')"),
    task: str = Form("transcribe", description="Tipo de tarea: 'transcribe' o 'translate'"),
    current_user: dict = Depends(get_api_key_user)  # Requiere API Key
) -> AudioToTextResponse:
    """
    Convierte un archivo de audio a texto usando faster-whisper (CTranslate2)
    
    Requiere autenticación mediante API Key (header: X-API-Key)
    
    - **audio_file**: Archivo de audio (formatos soportados: wav, mp3, m4a, etc.)
    - **language**: Código de idioma opcional ('es' para español, 'en' para inglés, 'auto' o None para detección automática)
    - **task**: 'transcribe' para transcribir o 'translate' para traducir al inglés
    
    Usa faster-whisper con modelo large-v3-turbo optimizado para español con cuantización int8 para máximo rendimiento.
    """
    # Leer el archivo de audio
    audio_bytes = await audio_file.read()
    request_body = {
        "filename": audio_file.filename,
        "content_type": audio_file.content_type,
        "audio_bytes": len(audio_bytes),
        "language": language,
        "task": task,
    }
    
    # Crear request DTO
    request = AudioToTextRequest(language=language, task=task)
    
    try:
        # Procesar (guardando el audio en carpeta antes de transcribir)
        response = await service.convert_audio_to_text(
            audio_file=audio_bytes,
            request=request,
            original_filename=audio_file.filename
        )
        logger.info(
            "audio-to-text OK | body=%s | response={text_len=%s, language=%s, duration=%s}",
            request_body,
            len(response.text or ""),
            response.language,
            response.duration,
        )
        return response
    except Exception as e:
        logger.exception(
            "audio-to-text ERROR | body=%s | response_error=%s",
            request_body,
            str(e),
        )
        raise


@router.post("/text-to-audio")
async def text_to_audio(
    request: TextToAudioRequest,
    current_user: dict = Depends(get_api_key_user)  # Requiere API Key
) -> Response:
    """
    Convierte texto a audio usando gTTS (Google Text-to-Speech)
    
    Requiere autenticación mediante API Key (header: X-API-Key)
    
    Retorna el audio directamente como archivo MP3 que se puede reproducir.
    """
    audio_bytes, duration = await service.convert_text_to_audio(request=request)
    
    # Retornar el audio directamente como archivo binario
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'inline; filename="audio.mp3"',
            "X-Audio-Duration": str(duration)
        }
    )
