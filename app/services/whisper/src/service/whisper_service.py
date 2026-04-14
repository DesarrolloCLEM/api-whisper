from app.services.whisper.src.model.whisper_dto import (
    AudioToTextRequest,
    AudioToTextResponse,
    TextToAudioRequest
)
from app.services.whisper.src.utils.audio_processor import AudioProcessor
from app.core.exceptions import APIException
from fastapi import status
from pathlib import Path
from typing import Optional
import base64
import re
import unicodedata
import io
import logging

logger = logging.getLogger(__name__)

_ASSETS_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "assets"
_GREETING_AUDIO_PATH = _ASSETS_DIR / "audios" / "esperanza_hola.mp3"

_GREETING_RE = re.compile(
    r"\b("
    r"hola|hey|hi"
    r"|buenos\s*d[ií]as?"
    r"|buenas\s*tardes"
    r"|buenas\s*noches"
    r"|buenas"
    r"|saludos"
    r"|qu[eé]\s*tal"
    r"|qu[eé]\s*hubo"
    r"|c[oó]mo\s*est[aá]s?"
    r")\b",
    re.IGNORECASE,
)

_MAX_GREETING_WORDS = 8


def _normalize_text(text: str) -> str:
    """Minúsculas y sin acentos para comparación uniforme."""
    lowered = text.lower().strip()
    nfkd = unicodedata.normalize("NFKD", lowered)
    return nfkd.encode("ascii", "ignore").decode("ascii")


def _is_greeting(text: str) -> bool:
    """True si el texto es un saludo corto sin contenido clínico relevante."""
    if not text or not text.strip():
        return False
    words = text.strip().split()
    if len(words) > _MAX_GREETING_WORDS:
        return False
    normalized = _normalize_text(text)
    return bool(_GREETING_RE.search(normalized))


def _load_greeting_audio_b64() -> Optional[str]:
    """Lee esperanza_hola.mp3 y lo codifica en base64. None si falla."""
    try:
        if not _GREETING_AUDIO_PATH.exists():
            logger.warning("Audio de saludo no encontrado en %s", _GREETING_AUDIO_PATH)
            return None
        return base64.b64encode(_GREETING_AUDIO_PATH.read_bytes()).decode("ascii")
    except Exception as exc:
        logger.warning("No se pudo leer audio de saludo: %s", exc)
        return None



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
        """Convierte audio a texto sin guardar en disco."""
        try:
            text, language, duration = await self.audio_processor.audio_to_text(
                audio_file=audio_file,
                language=request.language,
                task=request.task,
                original_filename=original_filename,
            )

            greeting_detected = _is_greeting(text)
            audio_b64: Optional[str] = None
            if greeting_detected:
                audio_b64 = _load_greeting_audio_b64()

            logger.info(
                "greeting_check | greeting_detected=%s | audio_attached=%s | text_preview=%r",
                greeting_detected,
                audio_b64 is not None,
                (text[:80] + "...") if len(text) > 80 else text,
            )

            return AudioToTextResponse(
                text=text,
                language=language,
                duration=duration,
                audio_base64=audio_b64,
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
