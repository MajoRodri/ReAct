from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.auth.auth import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    return decode_token(token)


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo el administrador puede realizar esta acción")
    return user
