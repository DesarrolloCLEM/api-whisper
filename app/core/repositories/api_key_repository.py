from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
from app.core.models import APIKey
from app.core.exceptions import APIException
from fastapi import status


class APIKeyRepository:
    """Repositorio para operaciones con API Keys"""
    
    @staticmethod
    def get_by_key(db: Session, key: str) -> Optional[APIKey]:
        """Obtiene una API key por su valor"""
        return db.query(APIKey).filter(APIKey.key == key).first()
    
    @staticmethod
    def get_by_id(db: Session, key_id: int) -> Optional[APIKey]:
        """Obtiene una API key por su ID"""
        return db.query(APIKey).filter(APIKey.id == key_id).first()
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[APIKey]:
        """Obtiene todas las API keys"""
        return db.query(APIKey).offset(skip).limit(limit).all()
    
    @staticmethod
    def create(
        db: Session,
        key: str,
        name: str,
        description: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> APIKey:
        """Crea una nueva API key"""
        api_key = APIKey(
            key=key,
            name=name,
            description=description,
            expires_at=expires_at
        )
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        return api_key
    
    @staticmethod
    def update_usage(db: Session, api_key: APIKey) -> APIKey:
        """Actualiza el uso de una API key"""
        api_key.last_used_at = datetime.utcnow()
        api_key.usage_count += 1
        db.commit()
        db.refresh(api_key)
        return api_key
    
    @staticmethod
    def deactivate(db: Session, key_id: int) -> APIKey:
        """Desactiva una API key"""
        api_key = APIKeyRepository.get_by_id(db, key_id)
        if not api_key:
            raise APIException(
                message="API key no encontrada",
                status_code=status.HTTP_404_NOT_FOUND
            )
        api_key.is_active = False
        db.commit()
        db.refresh(api_key)
        return api_key
    
    @staticmethod
    def activate(db: Session, key_id: int) -> APIKey:
        """Activa una API key"""
        api_key = APIKeyRepository.get_by_id(db, key_id)
        if not api_key:
            raise APIException(
                message="API key no encontrada",
                status_code=status.HTTP_404_NOT_FOUND
            )
        api_key.is_active = True
        db.commit()
        db.refresh(api_key)
        return api_key
    
    @staticmethod
    def delete(db: Session, key_id: int) -> bool:
        """Elimina una API key"""
        api_key = APIKeyRepository.get_by_id(db, key_id)
        if not api_key:
            raise APIException(
                message="API key no encontrada",
                status_code=status.HTTP_404_NOT_FOUND
            )
        db.delete(api_key)
        db.commit()
        return True
    
    @staticmethod
    def is_valid(api_key: APIKey) -> bool:
        """Valida si una API key es válida"""
        if not api_key:
            return False
        if not api_key.is_active:
            return False
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return False
        return True
