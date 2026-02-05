from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List
from app.core.repositories import APIKeyRepository
from app.services.api_keys.src.model.api_key_dto import (
    APIKeyCreateRequest,
    APIKeyCreateResponse,
    APIKeyResponse,
    APIKeyListResponse
)
from app.services.api_keys.src.utils.key_generator import generate_api_key
from app.core.exceptions import APIException
from fastapi import status


class APIKeyService:
    """Servicio para gestión de API Keys"""
    
    def __init__(self):
        self.repository = APIKeyRepository()
    
    async def create_api_key(
        self,
        db: Session,
        request: APIKeyCreateRequest
    ) -> APIKeyCreateResponse:
        """Crea una nueva API key"""
        # Generar API key única
        api_key_value = generate_api_key()
        
        # Verificar que no exista (muy poco probable pero por seguridad)
        while self.repository.get_by_key(db, api_key_value):
            api_key_value = generate_api_key()
        
        # Calcular fecha de expiración
        expires_at = None
        if request.expires_days:
            expires_at = datetime.utcnow() + timedelta(days=request.expires_days)
        
        # Crear API key
        api_key = self.repository.create(
            db=db,
            key=api_key_value,
            name=request.name,
            description=request.description,
            expires_at=expires_at
        )
        
        return APIKeyCreateResponse(
            id=api_key.id,
            key=api_key.key,
            name=api_key.name,
            description=api_key.description,
            created_at=api_key.created_at,
            expires_at=api_key.expires_at
        )
    
    async def list_api_keys(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> APIKeyListResponse:
        """Lista todas las API keys"""
        api_keys = self.repository.get_all(db, skip=skip, limit=limit)
        
        # Ocultar la key completa por seguridad (solo mostrar primeros caracteres)
        items = []
        for ak in api_keys:
            masked_key = f"{ak.key[:8]}...{ak.key[-4:]}" if len(ak.key) > 12 else "***"
            items.append(APIKeyResponse(
                id=ak.id,
                key=masked_key,
                name=ak.name,
                description=ak.description,
                is_active=ak.is_active,
                created_at=ak.created_at,
                expires_at=ak.expires_at,
                last_used_at=ak.last_used_at,
                usage_count=ak.usage_count
            ))
        
        return APIKeyListResponse(
            total=len(items),
            items=items
        )
    
    async def get_api_key(
        self,
        db: Session,
        key_id: int
    ) -> APIKeyResponse:
        """Obtiene una API key por ID"""
        api_key = self.repository.get_by_id(db, key_id)
        if not api_key:
            raise APIException(
                message="API key no encontrada",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Ocultar la key completa
        masked_key = f"{api_key.key[:8]}...{api_key.key[-4:]}" if len(api_key.key) > 12 else "***"
        
        return APIKeyResponse(
            id=api_key.id,
            key=masked_key,
            name=api_key.name,
            description=api_key.description,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            expires_at=api_key.expires_at,
            last_used_at=api_key.last_used_at,
            usage_count=api_key.usage_count
        )
    
    async def deactivate_api_key(
        self,
        db: Session,
        key_id: int
    ) -> APIKeyResponse:
        """Desactiva una API key"""
        api_key = self.repository.deactivate(db, key_id)
        masked_key = f"{api_key.key[:8]}...{api_key.key[-4:]}" if len(api_key.key) > 12 else "***"
        
        return APIKeyResponse(
            id=api_key.id,
            key=masked_key,
            name=api_key.name,
            description=api_key.description,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            expires_at=api_key.expires_at,
            last_used_at=api_key.last_used_at,
            usage_count=api_key.usage_count
        )
    
    async def activate_api_key(
        self,
        db: Session,
        key_id: int
    ) -> APIKeyResponse:
        """Activa una API key"""
        api_key = self.repository.activate(db, key_id)
        masked_key = f"{api_key.key[:8]}...{api_key.key[-4:]}" if len(api_key.key) > 12 else "***"
        
        return APIKeyResponse(
            id=api_key.id,
            key=masked_key,
            name=api_key.name,
            description=api_key.description,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            expires_at=api_key.expires_at,
            last_used_at=api_key.last_used_at,
            usage_count=api_key.usage_count
        )
    
    async def delete_api_key(
        self,
        db: Session,
        key_id: int
    ) -> dict:
        """Elimina una API key"""
        self.repository.delete(db, key_id)
        return {"message": "API key eliminada correctamente"}
