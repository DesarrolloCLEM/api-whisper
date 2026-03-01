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


class WhisperService:
    """Servicio para conversión de audio usando Whisper"""
    
    def __init__(self):
        self.audio_processor = AudioProcessor()
    
    def _extension_from_filename(self, filename: Optional[str]) -> str:
        if not filename or "." not in filename:
            return ".wav"
        return "." + filename.rsplit(".", 1)[-1].lower()

    async def convert_audio_to_text(
        self,
        audio_file: bytes,
        request: AudioToTextRequest,
        original_filename: Optional[str] = None
    ) -> AudioToTextResponse:
        """Convierte audio a texto. Guarda el audio en disco antes de transcribir."""
        try:
            settings = get_settings()
            upload_dir = Path(settings.audio_uploads_dir)
            upload_dir.mkdir(parents=True, exist_ok=True)
            ext = self._extension_from_filename(original_filename)
            unique_name = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
            save_path = upload_dir / unique_name
            save_path.write_bytes(audio_file)
            text, language, duration = await self.audio_processor.audio_to_text(
                audio_file=audio_file,
                language=request.language,
                task=request.task
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
