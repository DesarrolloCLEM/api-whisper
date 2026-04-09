from pydantic import BaseModel, Field
from typing import Optional


class AudioToTextRequest(BaseModel):
    """DTO para solicitud de conversión de audio a texto"""
    language: Optional[str] = Field(
        None, 
        description="Código de idioma (ej: 'es' para español, 'en' para inglés). Use 'auto' o None para detección automática"
    )
    task: str = Field("transcribe", description="Tipo de tarea: 'transcribe' para transcribir o 'translate' para traducir al inglés")
    
    class Config:
        json_schema_extra = {
            "example": {
                "language": "es",
                "task": "transcribe"
            }
        }


class AudioToTextResponse(BaseModel):
    """DTO para respuesta de conversión de audio a texto"""
    text: str
    language: Optional[str] = None
    duration: float
    audio_base64: Optional[str] = Field(
        None,
        description="Audio pregrabado en base64 (presente solo cuando se detecta saludo corto)",
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hola, este es un ejemplo de transcripción",
                "language": "es",
                "duration": 5.2,
                "audio_base64": None
            }
        }


class TextToAudioRequest(BaseModel):
    """DTO para solicitud de conversión de texto a audio"""
    text: str = Field(..., min_length=1, max_length=5000, description="Texto a convertir")
    language: Optional[str] = Field(None, description="Código de idioma (ej: 'es', 'en')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hola, este es un ejemplo de texto a audio",
                "language": "es"
            }
        }


class TextToAudioResponse(BaseModel):
    """DTO para respuesta de conversión de texto a audio"""
    audio_base64: str
    format: str = "mp3"  # gTTS genera MP3
    duration: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "audio_base64": "UklGRiQAAABXQVZFZm10...",
                "format": "wav",
                "duration": 3.5
            }
        }
