from datetime import datetime
from app.services.health.src.model.health_dto import HealthResponse
from app.config import get_settings


class HealthService:
    """Servicio para verificar el estado de la API"""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def check_health(self) -> HealthResponse:
        """Verifica el estado de salud de la API"""
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now(),
            version=self.settings.api_version,
            service="whisper-api"
        )
