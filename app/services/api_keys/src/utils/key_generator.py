import secrets
import string
from app.config import get_settings


def generate_api_key(prefix: str = "sk_") -> str:
    """
    Genera una API key segura
    
    Args:
        prefix: Prefijo para la API key (ej: 'sk_', 'pk_')
    
    Returns:
        API key generada
    """
    settings = get_settings()
    
    # Generar parte aleatoria
    alphabet = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(settings.api_key_length))
    
    # Combinar prefijo + parte aleatoria
    api_key = f"{prefix}{random_part}"
    
    return api_key
