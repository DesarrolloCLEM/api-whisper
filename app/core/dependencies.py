from fastapi import Depends, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.config import get_settings
from app.core.database import get_db
from app.core.repositories import APIKeyRepository
from app.core.exceptions import APIException
from fastapi import status

settings = get_settings()


async def get_api_key_user(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> dict:
    """
    Valida el API Key y retorna información del usuario
    """
    if not x_api_key:
        raise APIException(
            message="API Key requerida",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details={"header": "X-API-Key"}
        )
    
    # Buscar API key en BD
    api_key = APIKeyRepository.get_by_key(db, x_api_key)
    
    # Validar API key
    if not APIKeyRepository.is_valid(api_key):
        raise APIException(
            message="API Key inválida o expirada",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Actualizar uso
    APIKeyRepository.update_usage(db, api_key)
    
    return {
        "api_key_id": api_key.id,
        "name": api_key.name,
        "auth_type": "api_key"
    }
