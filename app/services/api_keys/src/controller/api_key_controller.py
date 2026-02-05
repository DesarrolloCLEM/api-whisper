from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.api_keys.src.service import APIKeyService
from app.services.api_keys.src.model import (
    APIKeyCreateRequest,
    APIKeyCreateResponse,
    APIKeyResponse,
    APIKeyListResponse
)

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

service = APIKeyService()


@router.post("", response_model=APIKeyCreateResponse, status_code=201)
async def create_api_key(
    request: APIKeyCreateRequest,
    db: Session = Depends(get_db)
) -> APIKeyCreateResponse:
    """
    Crea una nueva API key
    
    ⚠️ **Importante**: La API key completa solo se mostrará una vez al crearla.
    Guárdala de forma segura.
    """
    return await service.create_api_key(db, request)


@router.get("", response_model=APIKeyListResponse)
async def list_api_keys(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
) -> APIKeyListResponse:
    """Lista todas las API keys (las keys están enmascaradas por seguridad)"""
    return await service.list_api_keys(db, skip=skip, limit=limit)


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: int,
    db: Session = Depends(get_db)
) -> APIKeyResponse:
    """Obtiene una API key por ID (la key está enmascarada por seguridad)"""
    return await service.get_api_key(db, key_id)


@router.post("/{key_id}/deactivate", response_model=APIKeyResponse)
async def deactivate_api_key(
    key_id: int,
    db: Session = Depends(get_db)
) -> APIKeyResponse:
    """Desactiva una API key"""
    return await service.deactivate_api_key(db, key_id)


@router.post("/{key_id}/activate", response_model=APIKeyResponse)
async def activate_api_key(
    key_id: int,
    db: Session = Depends(get_db)
) -> APIKeyResponse:
    """Activa una API key"""
    return await service.activate_api_key(db, key_id)


@router.delete("/{key_id}")
async def delete_api_key(
    key_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """Elimina permanentemente una API key"""
    return await service.delete_api_key(db, key_id)
