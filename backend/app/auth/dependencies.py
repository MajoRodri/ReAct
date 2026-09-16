"""Dependencias FastAPI para proteger rutas con autenticación y control de roles."""

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.auth.auth import decode_token

# auto_error=False permite devolver 401 personalizado en lugar del genérico de FastAPI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Extrae y valida el JWT del header Authorization; devuelve el payload como dict."""
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    return decode_token(token)


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Restringe el acceso a usuarios con role='admin'; lanza 403 en caso contrario."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo el administrador puede realizar esta acción")
    return user
