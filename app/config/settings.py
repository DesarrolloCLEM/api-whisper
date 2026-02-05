from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # API Configuration
    api_title: str = "Whisper API"
    api_version: str = "1.0.0"
    api_description: str = "API para conversión de audio a texto y texto a audio usando Whisper"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Database Configuration (SQLite para API keys)
    database_url: str = "sqlite:///./api_keys.db"
    
    # Whisper Configuration (faster-whisper)
    whisper_model: str = "large-v3-turbo"  # Mejor modelo para español
    whisper_device: str = "cpu"  # "cpu" o "cuda"
    whisper_compute_type: str = "int8"  # "int8" para CPU (más rápido), "float16" para GPU
    whisper_language: str = "es"  # Idioma por defecto (español)
    whisper_num_workers: int = 1  # Número de workers para procesamiento
    hf_token: str = ""  # Token opcional de Hugging Face para descargas más rápidas (opcional)
    
    # TTS Configuration (Text-to-Speech)
    tts_provider: str = "google"  # "google" para gTTS o "elevenlabs" para ElevenLabs
    elevenlabs_api_key: str = ""  # API Key de ElevenLabs (requerida si tts_provider=elevenlabs)
    elevenlabs_voice_id: str = ""  # Voice ID de ElevenLabs (se selecciona automáticamente según idioma si está vacío)
    
    # API Key Configuration
    api_key_header_name: str = "X-API-Key"
    api_key_length: int = 32
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Obtiene la configuración de la aplicación (cached)"""
    return Settings()
