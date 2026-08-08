"""LabLens AI - Security Utilities"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from jose import JWTError, jwt
import bcrypt
from cryptography.fernet import Fernet
from app.core.config import get_settings
import secrets
import hashlib
import base64


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


def generate_secure_filename(original: str) -> str:
    ext = original.rsplit(".", 1)[-1].lower() if "." in original else "bin"
    token = secrets.token_urlsafe(16)
    return f"{token}.{ext}"


def generate_signed_url_path(report_id: str, user_id: str, expiry_hours: int = 24) -> str:
    settings = get_settings()
    expiry = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)
    data = f"{report_id}:{user_id}:{expiry.timestamp()}"
    signature = hashlib.sha256(f"{data}:{settings.secret_key}".encode()).hexdigest()[:32]
    return f"{report_id}?sig={signature}&exp={int(expiry.timestamp())}"


_encryption_key_cache: Optional[bytes] = None


def get_encryption_key() -> bytes:
    global _encryption_key_cache
    if _encryption_key_cache is not None:
        return _encryption_key_cache
    settings = get_settings()
    if settings.encryption_key:
        key = settings.encryption_key.encode()
    else:
        import hashlib
        raw = hashlib.sha256(settings.secret_key.encode()).digest()
        key = base64.urlsafe_b64encode(raw)
    _encryption_key_cache = key
    return key


def encrypt_file_data(data: bytes) -> bytes:
    f = Fernet(get_encryption_key())
    return f.encrypt(data)


def decrypt_file_data(data: bytes) -> bytes:
    f = Fernet(get_encryption_key())
    return f.decrypt(data)
