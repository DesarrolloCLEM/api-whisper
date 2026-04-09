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
import base64
import re
import unicodedata
import uuid
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
