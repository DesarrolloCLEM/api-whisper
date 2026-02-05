from fastapi import APIRouter
from app.services.health.src.service import HealthService
from app.services.health.src.model import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])

service = HealthService()


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Endpoint para verificar el estado de la API"""
    return await service.check_health()
