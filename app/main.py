import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config import get_settings
from app.core.exceptions import APIException, exception_handler
from app.core.database import Base, engine
from app.services.health.src.controller import router as health_router
from app.services.api_keys.src.controller import router as api_keys_router
from app.services.whisper.src.controller import router as whisper_router

logger = logging.getLogger("uvicorn.error")

# Obtener configuración
settings = get_settings()

# Crear tablas de BD
Base.metadata.create_all(bind=engine)

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    debug=settings.debug
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar manejador de excepciones
app.add_exception_handler(APIException, exception_handler)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Log detallado para 422 Unprocessable Entity (errores de validación)."""
    body = b""
    try:
        body = await request.body()
    except Exception:
        pass
    body_preview = body.decode("utf-8", errors="replace")[:500] if body else "(vacío)"
    errors = exc.errors()
    logger.warning(
        "422 Validation Error | path=%s %s | content_type=%s | body_preview=%s | errors=%s",
        request.method,
        request.url.path,
        request.headers.get("content-type", ""),
        body_preview,
        errors,
    )
    # Mensaje más legible en consola
    for i, err in enumerate(errors, 1):
        loc = " -> ".join(str(x) for x in err.get("loc", ()))
        msg = err.get("msg", "")
        logger.warning("  [%d] %s: %s", i, loc, msg)
    return JSONResponse(
        status_code=422,
        content={"detail": errors},
    )


app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Registrar routers de servicios
app.include_router(health_router)
app.include_router(api_keys_router)
app.include_router(whisper_router)


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Whisper API",
        "version": settings.api_version,
        "docs": "/docs",
        "authentication": {
            "api_key": "Usa header X-API-Key"
        }
    }


# Ejecutar servidor si se ejecuta directamente
if __name__ == "__main__":
    import uvicorn
    
    # Mostrar información clara antes de iniciar
    print("\n" + "="*60)
    print("🚀 Whisper API - Iniciando servidor")
    print("="*60)
    print(f"📋 Título: {settings.api_title}")
    print(f"📦 Versión: {settings.api_version}")
    print(f"🌐 Host: {settings.host}")
    print(f"🔌 Puerto: {settings.port}")
    print(f"🐛 Modo Debug: {'✅ Activado' if settings.debug else '❌ Desactivado'}")
    print(f"🤖 Modelo Whisper: {settings.whisper_model}")
    print(f"🌍 Idioma por defecto: {settings.whisper_language}")
    print("="*60)
    print(f"\n✅ Servidor corriendo en:")
    print(f"   🔗 Local:    http://127.0.0.1:{settings.port}")
    print(f"   🌐 Red:      http://{settings.host}:{settings.port}")
    print(f"   📚 Docs:     http://127.0.0.1:{settings.port}/docs")
    print(f"   📖 ReDoc:    http://127.0.0.1:{settings.port}/redoc")
    print("\n" + "="*60)
    print("Presiona CTRL+C para detener el servidor\n")
    print("="*60 + "\n")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
