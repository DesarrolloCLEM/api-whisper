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

router = APIRouter(prefix="/whisper", tags=["Whisper"])

service = WhisperService()


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
    
    # Crear request DTO
    request = AudioToTextRequest(language=language, task=task)
    
    # Procesar (guardando el audio en carpeta antes de transcribir)
    return await service.convert_audio_to_text(
        audio_file=audio_bytes,
        request=request,
        original_filename=audio_file.filename
    )


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
