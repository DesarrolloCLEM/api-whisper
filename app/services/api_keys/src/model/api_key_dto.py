from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class APIKeyCreateRequest(BaseModel):
    """DTO para crear una API key"""
    name: str = Field(..., min_length=1, max_length=100, description="Nombre de la API key")
    description: Optional[str] = Field(None, max_length=500, description="Descripción opcional")
    expires_days: Optional[int] = Field(None, ge=1, description="Días hasta expiración")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Cliente Producción",
                "description": "API key para cliente en producción",
                "expires_days": 365
            }
        }


class APIKeyResponse(BaseModel):
    """DTO para respuesta de API key"""
    id: int
    key: str
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "key": "sk_live_1234567890abcdef",
                "name": "Cliente Producción",
                "description": "API key para cliente en producción",
                "is_active": True,
                "created_at": "2026-02-05T10:00:00",
                "expires_at": "2027-02-05T10:00:00",
                "last_used_at": "2026-02-05T12:00:00",
                "usage_count": 150
            }
        }


class APIKeyCreateResponse(BaseModel):
    """DTO para respuesta de creación de API key"""
    id: int
    key: str
    name: str
    description: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]
    message: str = "Guarda esta API key, no se mostrará nuevamente"
    
    class Config:
        from_attributes = True


class APIKeyListResponse(BaseModel):
    """DTO para lista de API keys"""
    total: int
    items: list[APIKeyResponse]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 2,
                "items": []
            }
        }
