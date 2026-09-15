from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException

SECRET_KEY = "react-triage-escolar-secret-2024"
ALGORITHM  = "HS256"
TOKEN_HOURS = 8

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(
    username: str,
    role: str,
    department: str | None,
    name: str,
    institution_code: str | None = None,
    temp_password: bool = False,
) -> str:
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
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
