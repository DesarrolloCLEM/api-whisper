import io
import logging
import tempfile
import os
from typing import Optional, Tuple
from faster_whisper import WhisperModel
from app.config import get_settings

logger = logging.getLogger(__name__)


def _temp_suffix_from_filename(filename: Optional[str]) -> str:
    """Extensión coherente con el contenido (evita meter M4A en un .wav)."""
    if not filename or "." not in filename:
        return ".m4a"
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext in ("mp3", "m4a", "aac", "wav", "ogg", "flac"):
        return f".{ext}"
    return ".m4a"


class AudioProcessor:
    """Procesador de audio usando faster-whisper (CTranslate2)"""
    
    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self._model_loaded = False
    
    def _load_model(self):
        """Carga el modelo de faster-whisper (lazy loading)"""
        if not self._model_loaded:
            device = self.settings.whisper_device
            compute_type = self.settings.whisper_compute_type
            
            # Para CPU, usar int8 es más rápido
            # Para GPU, usar float16 es más preciso
            if device == "cpu" and compute_type not in ["int8", "int8_float16"]:
                compute_type = "int8"
            elif device == "cuda" and compute_type == "int8":
                compute_type = "float16"
            
            # Configurar token de Hugging Face si está disponible
            download_kwargs = {}
            if self.settings.hf_token:
                download_kwargs["token"] = self.settings.hf_token
            
            self.model = WhisperModel(
                self.settings.whisper_model,
                device=device,
                compute_type=compute_type,
                num_workers=self.settings.whisper_num_workers,
                download_root=None,  # Usar caché por defecto
                **download_kwargs
            )
            self._model_loaded = True
    
    async def audio_to_text(
        self,
        audio_file: bytes,
        language: Optional[str] = None,
        task: str = "transcribe",
        original_filename: Optional[str] = None,
    ) -> Tuple[str, Optional[str], float]:
        """
        Convierte audio a texto usando faster-whisper
        
        Args:
            audio_file: Bytes del archivo de audio
            language: Código de idioma (ej: 'es', 'en'). Si es None, usa el configurado o detecta automáticamente
            task: 'transcribe' para transcribir o 'translate' para traducir al inglés
        
        Returns:
            Tuple[str, Optional[str], float]: (texto, idioma detectado, duración)
        """
        # Cargar modelo si no está cargado
        self._load_model()
        
        # Manejar idioma: usar el especificado, el configurado, o None para auto-detección
        if language is None or language == "auto":
            # Si no se especifica idioma, usar el configurado o None para auto-detección
            language_param = None if self.settings.whisper_language == "auto" else self.settings.whisper_language
        else:
            language_param = language
        
        # Crear archivo temporal para faster-whisper
        # faster-whisper necesita un archivo en disco o usar numpy array
        tmp_suffix = _temp_suffix_from_filename(original_filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix=tmp_suffix) as tmp_file:
            tmp_file.write(audio_file)
            tmp_file_path = tmp_file.name
        
        try:
            # Verificar si onnxruntime está disponible para VAD
            try:
                import onnxruntime
                vad_available = True
            except ImportError:
                vad_available = False
            
            # Transcribir usando faster-whisper
            transcribe_kwargs = {
                "language": language_param,
                "task": task,
                "beam_size": 5,  # Balance entre velocidad y precisión
            }
            
            # VAD opcional: con voz baja o clips cortos suele dejar casi silencio → alucinaciones del modelo
            if vad_available and self.settings.whisper_vad_filter:
                transcribe_kwargs["vad_filter"] = True
                transcribe_kwargs["vad_parameters"] = dict(min_silence_duration_ms=500)

            logger.info(
                "WHISPER_STT_IN | archivo_tmp=%s | bytes_entrada=%s | language_param=%s | task=%s | "
                "vad_filter=%s | modelo=%s",
                tmp_file_path,
                len(audio_file),
                language_param,
                task,
                transcribe_kwargs.get("vad_filter", False),
                self.settings.whisper_model,
            )

            segments, info = self.model.transcribe(
                tmp_file_path,
                **transcribe_kwargs
            )

            # Obtener idioma detectado
            detected_language = info.language if hasattr(info, 'language') else language_param or "unknown"

            # Concatenar todos los segmentos (aquí se construye el texto final que verá el cliente)
            text_segments = []
            duration = 0.0

            for idx, segment in enumerate(segments):
                piece = (segment.text or "").strip()
                text_segments.append(segment.text)
                duration = max(duration, segment.end)
                logger.info(
                    "WHISPER_STT_SEGMENT | idx=%s | start=%.3f | end=%.3f | texto_segmento=%r",
                    idx,
                    segment.start,
                    segment.end,
                    piece,
                )

            text = " ".join(text_segments).strip()

            logger.info(
                "WHISPER_STT_OUT | idioma_detectado=%s | duracion_audio_s=%.3f | "
                "texto_completo_generado_por_modelo=%r",
                detected_language,
                duration,
                text,
            )

            return text, detected_language, duration
        finally:
            # Limpiar archivo temporal
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    async def _text_to_audio_google(
        self,
        text: str,
        language: str
    ) -> Tuple[bytes, float]:
        """Genera audio usando gTTS (Google Text-to-Speech)"""
        from gtts import gTTS
        
        # Crear objeto gTTS
        tts = gTTS(text=text, lang=language, slow=False)
        
        # Generar audio en memoria (MP3)
        mp3_buffer = io.BytesIO()
        try:
            tts.write_to_fp(mp3_buffer)
            mp3_buffer.seek(0)
            
            # Obtener bytes del audio MP3
            audio_bytes = mp3_buffer.getvalue()
            
            # Validar que se generó audio
            if not audio_bytes or len(audio_bytes) < 100:
                raise ValueError("No se pudo generar el audio o el archivo está vacío")
            
            # Estimar duración basada en la longitud del texto
            # gTTS habla aproximadamente a 150 palabras por minuto
            words = len(text.split())
            estimated_duration = (words / 150.0) * 60.0  # Convertir a segundos
            
            return audio_bytes, estimated_duration
        finally:
            mp3_buffer.close()
    
    async def _text_to_audio_elevenlabs(
        self,
        text: str,
        language: Optional[str] = None
    ) -> Tuple[bytes, float]:
        """Genera audio usando ElevenLabs"""
        try:
            from elevenlabs.client import ElevenLabs
        except ImportError:
            raise ImportError(
                "ElevenLabs no está instalado. Ejecuta: pip install elevenlabs"
            )
        
        # Validar API key
        if not self.settings.elevenlabs_api_key:
            raise ValueError(
                "ELEVENLABS_API_KEY no está configurada en el archivo .env"
            )
        
        # Crear cliente de ElevenLabs
        client = ElevenLabs(api_key=self.settings.elevenlabs_api_key)
        
        # Seleccionar voice_id según idioma si no está configurado
        voice_id = self.settings.elevenlabs_voice_id
        
        if not voice_id:
            # Intentar obtener una voz disponible del usuario
            # Los usuarios gratuitos deben usar sus propias voces creadas
            try:
                voices = client.voices.get_all()
                if voices.voices:
                    # Usar la primera voz disponible del usuario
                    voice_id = voices.voices[0].voice_id
                else:
                    raise ValueError(
                        "No tienes voces disponibles. "
                        "Los usuarios gratuitos de ElevenLabs deben crear sus propias voces. "
                        "Visita https://elevenlabs.io/app/voice-library para crear una voz, "
                        "o cambia TTS_PROVIDER a 'google' en el archivo .env"
                    )
            except Exception as e:
                raise ValueError(
                    f"No se pudo obtener una voz disponible. "
                    f"Los usuarios gratuitos de ElevenLabs deben usar sus propias voces creadas. "
                    f"Visita https://elevenlabs.io/app/voice-library para crear una voz, "
                    f"o cambia TTS_PROVIDER a 'google' en el archivo .env. "
                    f"Error: {str(e)}"
                )
        
        try:
            # Generar audio usando ElevenLabs
            audio_generator = client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id="eleven_multilingual_v2"  # Modelo que soporta múltiples idiomas
            )
            
            # Convertir el generador a bytes
            audio_bytes = b"".join(audio_generator)
            
            # Validar que se generó audio
            if not audio_bytes or len(audio_bytes) < 100:
                raise ValueError("No se pudo generar el audio o el archivo está vacío")
            
            # Estimar duración (ElevenLabs no retorna duración directamente)
            # Aproximadamente 150 palabras por minuto
            words = len(text.split())
            estimated_duration = (words / 150.0) * 60.0
            
            return audio_bytes, estimated_duration
        
        except Exception as e:
            # Manejar errores de ElevenLabs
            error_msg = str(e)
            error_str_lower = error_msg.lower()
            
            # Detectar errores de pago/suscripción
            if "payment_required" in error_str_lower or "402" in error_msg or "free users cannot use library voices" in error_str_lower:
                raise ValueError(
                    f"La voz seleccionada requiere una suscripción de pago. "
                    f"Opciones:\n"
                    f"1. Usa una voz personalizada que hayas creado (configura ELEVENLABS_VOICE_ID con su ID)\n"
                    f"2. Cambia TTS_PROVIDER a 'google' en el archivo .env para usar Google TTS (gratis)\n"
                    f"3. Actualiza tu suscripción de ElevenLabs\n"
                    f"Error original: {error_msg}"
                )
            else:
                raise ValueError(f"Error al generar audio con ElevenLabs: {error_msg}")
    
    async def text_to_audio(
        self,
        text: str,
        language: Optional[str] = None
    ) -> Tuple[bytes, float]:
        """
        Convierte texto a audio usando el proveedor configurado (Google TTS o ElevenLabs)
        
        Args:
            text: Texto a convertir a audio
            language: Código de idioma (ej: 'es' para español, 'en' para inglés)
        
        Returns:
            Tuple[bytes, float]: (audio_bytes en formato MP3, duración estimada en segundos)
        """
        # Usar idioma por defecto si no se especifica
        if language is None:
            language = self.settings.whisper_language
        
        # Validar que el idioma esté configurado
        if not language or language == "auto":
            language = "es"  # Español por defecto
        
        # Seleccionar proveedor según configuración
        provider = self.settings.tts_provider.lower()
        
        if provider == "elevenlabs":
            return await self._text_to_audio_elevenlabs(text, language)
        elif provider == "google":
            return await self._text_to_audio_google(text, language)
        else:
            raise ValueError(
                f"Proveedor TTS no válido: {provider}. "
                f"Usa 'google' o 'elevenlabs' en TTS_PROVIDER"
            )
