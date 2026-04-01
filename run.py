"""
Script para ejecutar el servidor usando configuración del .env
"""
import uvicorn
from app.config import get_settings

# Logs con fecha y hora (access + mensajes INFO de uvicorn).
_UVICORN_LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(asctime)s %(levelprefix)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": True,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(asctime)s %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": True,
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
        # Sin esto, los logger.info de app.* no aparecen (solo access de uvicorn).
        "app": {"handlers": ["default"], "level": "INFO", "propagate": False},
    },
    "root": {"handlers": ["default"], "level": "INFO"},
}

if __name__ == "__main__":
    settings = get_settings()
    
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
        log_level="info",
        log_config=_UVICORN_LOG_CONFIG,
    )
