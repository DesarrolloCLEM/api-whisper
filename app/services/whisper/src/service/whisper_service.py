from app.services.whisper.src.model.whisper_dto import (
    AudioToTextRequest,
    AudioToTextResponse,
    TextToAudioRequest
)
from app.services.whisper.src.utils.audio_processor import AudioProcessor
from app.core.exceptions import APIException
from app.config import get_settings
from fastapi import status
from pathlib import Path
from datetime import datetime
from typing import Optional
import uuid
import io
import logging

logger = logging.getLogger(__name__)


def _audio_bytes_to_mp3(audio_bytes: bytes, input_format: str = "m4a") -> bytes:
    """Convierte bytes de audio (m4a, wav, etc.) a MP3 usando pydub. Requiere ffmpeg."""
    from pydub import AudioSegment
    segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format=input_format)
    mp3_io = io.BytesIO()
    segment.export(mp3_io, format="mp3")
    mp3_io.seek(0)
    return mp3_io.getvalue()


def _guess_audio_format(filename: Optional[str]) -> str:
    """Devuelve el formato para pydub según la extensión del archivo."""
    if not filename or "." not in filename:
        return "m4a"
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext in ("mp3", "m4a", "aac", "wav", "ogg", "flac"):
        return ext
    return "m4a"


class WhisperService:
    """Servicio para conversión de audio usando Whisper"""
    
    def __init__(self):
        self.audio_processor = AudioProcessor()

    async def convert_audio_to_text(
        self,
        audio_file: bytes,
        request: AudioToTextRequest,
        original_filename: Optional[str] = None
    ) -> AudioToTextResponse:
        """Convierte audio a texto. Guarda el audio en disco como MP3."""
        try:
            settings = get_settings()
            upload_dir = Path(settings.audio_uploads_dir)
            upload_dir.mkdir(parents=True, exist_ok=True)

            # Intentar guardar como MP3; si falla (ej. ffmpeg no instalado), guardar en formato original
            save_ext = ".mp3"
            bytes_to_save = audio_file
            input_fmt = _guess_audio_format(original_filename)
            try:
                bytes_to_save = _audio_bytes_to_mp3(audio_file, input_format=input_fmt)
            except Exception as e:
                save_ext = f".{input_fmt}"
                logger.warning(
                    "No se pudo convertir a MP3 (¿ffmpeg instalado?). Se guarda como %s. Detalle: %s",
                    save_ext, e
                )

            unique_name = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{save_ext}"
            save_path = upload_dir / unique_name
            save_path.write_bytes(bytes_to_save)

            # Transcribir con los bytes originales (faster-whisper acepta m4a, wav, etc.)
            text, language, duration = await self.audio_processor.audio_to_text(
                audio_file=audio_file,
                language=request.language,
                task=request.task,
                original_filename=original_filename,
            )

            return AudioToTextResponse(
                text=text,
                language=language,
                duration=duration
            )
        except Exception as e:
            raise APIException(
                message=f"Error al procesar el audio: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    async def convert_text_to_audio(
        self,
        request: TextToAudioRequest
    ) -> tuple[bytes, float]:
        """
        Convierte texto a audio
        
        Returns:
            tuple[bytes, float]: (audio_bytes en formato MP3, duración en segundos)
        """
        try:
            audio_bytes, duration = await self.audio_processor.text_to_audio(
                text=request.text,
                language=request.language
            )
            
            return audio_bytes, duration
        except Exception as e:
            raise APIException(
                message=f"Error al procesar el texto: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
