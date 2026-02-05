from fastapi import Request, status
from fastapi.responses import JSONResponse
from typing import Optional


class APIException(Exception):
    """Excepción base para la API"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[dict] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


async def exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Manejador global de excepciones"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "details": exc.details
        }
    )
