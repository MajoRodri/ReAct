"""Utilidades de autenticación: hashing de contraseñas y JWT."""

import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException

# SECRET_KEY se lee del entorno; el valor por defecto es solo para desarrollo local
SECRET_KEY  = os.environ.get("SECRET_KEY", "react-triage-escolar-secret-2024-CHANGE-ME")
ALGORITHM   = "HS256"
TOKEN_HOURS = 8  # duración de la sesión JWT

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Devuelve el hash bcrypt de una contraseña en texto plano."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Comprueba que `plain` coincide con el hash almacenado en BD."""
    return pwd_context.verify(plain, hashed)


def create_token(
    username: str,
    role: str,
    department: str | None,
    name: str,
    institution_code: str | None = None,
    temp_password: bool = False,
) -> str:
    """Genera un JWT firmado con los claims de identidad del usuario.

    Incluye `institution_code` y `temp_password` para que el frontend
    pueda forzar el cambio de clave sin llamadas adicionales al backend.
    """
    payload = {
        "sub":              username,
        "role":             role,
        "department":       department,
        "name":             name,
        "institution_code": institution_code,
        "temp_password":    temp_password,
        "exp":              datetime.utcnow() + timedelta(hours=TOKEN_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decodifica y verifica la firma del JWT; lanza 401 si es inválido o expirado."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
