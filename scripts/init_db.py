"""
Script para inicializar la base de datos
Ejecutar con: python -m scripts.init_db
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar app
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import Base, engine
from app.core.models import APIKey

def init_db():
    """Crea todas las tablas en la base de datos"""
    print("Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("✅ Base de datos inicializada correctamente")

if __name__ == "__main__":
    init_db()
