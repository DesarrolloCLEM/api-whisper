from app.services.whisper.src.model.whisper_dto import (
    AudioToTextRequest,
    AudioToTextResponse,
    TextToAudioRequest
)
from app.services.whisper.src.utils.audio_processor import AudioProcessor
from app.core.exceptions import APIException
from fastapi import status


class WhisperService:
    """Servicio para conversión de audio usando Whisper"""
    
    def __init__(self):
        self.audio_processor = AudioProcessor()
    
    async def convert_audio_to_text(
        self,
        audio_file: bytes,
        request: AudioToTextRequest
    ) -> AudioToTextResponse:
        """Convierte audio a texto"""
        try:
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
