import time
import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def create_access_token(sub: str, minutes: int | None = None) -> str:
    """
    Crea un token JWT de acceso para el usuario identificado por ``sub``.

    Pydantic normaliza las variables de entorno a atributos en minúsculas
    (por ejemplo, ``SECRET_KEY`` -> ``secret_key``), así que debemos
    acceder a los atributos correspondientes en minúsculas.

    Args:
        sub: ID del usuario que se codifica en el token.
        minutes: Duración del token en minutos. Si no se especifica,
            se tomará el valor por defecto definido en la configuración.

    Returns:
        Una cadena JWT codificada con HS256.
    """
    # Usa el valor por defecto de configuración si no se provee `minutes`
    expire_minutes = minutes or settings.access_token_expire_minutes
    expire = int(time.time()) + 60 * expire_minutes
    payload = {"sub": sub, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
