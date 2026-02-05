from pydantic import BaseModel
from datetime import datetime


class HealthResponse(BaseModel):
    """DTO para respuesta de health check"""
    status: str
    timestamp: datetime
    version: str
    service: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2026-02-05T10:00:00",
                "version": "1.0.0",
                "service": "whisper-api"
            }
        }
