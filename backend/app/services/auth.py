# backend/services/auth.py
from fastapi import Depends, status, Cookie, Request, Header
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt, ExpiredSignatureError
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.models import User
from app.schemas import TokenData
from app.config import settings
from app.services.security_logging import log_unauthorized_access

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    # Aggiungi claim standard JWT
    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.utcnow(),  # Issued At
            "iss": settings.JWT_ISSUER,  # Issuer
            "aud": settings.JWT_AUDIENCE,  # Audience
            "type": "access",  # Token type
        }
    )

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    logger.info(f"Token created for user {data.get('sub')} with expiration {expire}")
    return encoded_jwt


def create_mfa_pending_token(user_id: str, tenant_id: str) -> str:
    """Short-lived token issued after password OK when MFA verification is still required."""
    expire = datetime.utcnow() + timedelta(minutes=settings.MFA_PENDING_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "type": "mfa_pending",
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_mfa_setup_token(user_id: str, tenant_id: str) -> str:
    """Short-lived token allowing MFA enrollment when policy forces setup before access."""
    expire = datetime.utcnow() + timedelta(minutes=settings.MFA_PENDING_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "type": "mfa_setup",
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_typed_token(token: str, expected_type: str) -> dict:
    """Decode JWT and require a specific type claim."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
    except ExpiredSignatureError:
        raise ErrorCodeException(
            status_code=401, error_code=ErrorCode.MFA_TOKEN_EXPIRED
        )
    except JWTError:
        raise ErrorCodeException(status_code=401, error_code=ErrorCode.INVALID_TOKEN)

    if payload.get("type") != expected_type:
        raise ErrorCodeException(status_code=401, error_code=ErrorCode.INVALID_TOKEN)
    if not payload.get("sub"):
        raise ErrorCodeException(status_code=401, error_code=ErrorCode.INVALID_TOKEN)
    return payload


async def get_current_user(
    request: Request,
    authorization: str = Header(None),
    access_token_cookie: str = Cookie(None),
    db: Session = Depends(get_db),
):
    token = None

    # Try to get token from Authorization header (Bearer)
    if authorization:
        scheme, _, param = authorization.partition(" ")
        if scheme.lower() == "bearer":
            token = param

    # Se non c’è header, provo a leggere il cookie
    if token is None and access_token_cookie:
        token = access_token_cookie

    if token is None:
        log_unauthorized_access(request, reason="NO_TOKEN")
        raise ErrorCodeException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=ErrorCode.INVALID_CREDENTIALS,
        )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
        user_id: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")

        # Verifica che il token sia del tipo corretto
        token_type = payload.get("type")
        if token_type != "access":
            logger.warning(f"Token di tipo non valido: {token_type}")
            raise ErrorCodeException(
                status_code=401, error_code=ErrorCode.INVALID_TOKEN
            )

        if user_id is None:
            logger.warning("Token senza user_id")
            raise ErrorCodeException(
                status_code=401, error_code=ErrorCode.INVALID_TOKEN
            )

    except ExpiredSignatureError:
        logger.info("Token scaduto")
        raise ErrorCodeException(status_code=401, error_code=ErrorCode.EXPIRED_TOKEN)
    except JWTError as e:
        logger.warning(f"Errore JWT generico: {e}")
        raise ErrorCodeException(status_code=401, error_code=ErrorCode.INVALID_TOKEN)

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise ErrorCodeException(status_code=401, error_code=ErrorCode.USER_NOT_FOUND)
    
    # Check if user is deleted
    if user.deleted_at is not None:
        raise ErrorCodeException(status_code=401, error_code=ErrorCode.USER_NOT_FOUND)

    # Deactivated users must not keep using active sessions.
    if not user.is_active:
        raise ErrorCodeException(status_code=401, error_code=ErrorCode.ACCESS_DENIED)
    
    return user


async def get_current_user_or_mfa_setup(
    request: Request,
    authorization: str = Header(None),
    access_token_cookie: str = Cookie(None),
    db: Session = Depends(get_db),
):
    """
    Accept either a normal access token or a short-lived mfa_setup token.
    Used for MFA enrollment endpoints when policy forces setup before full access.
    """
    token = None
    if authorization:
        scheme, _, param = authorization.partition(" ")
        if scheme.lower() == "bearer":
            token = param
    if token is None and access_token_cookie:
        token = access_token_cookie
    if token is None:
        log_unauthorized_access(request, reason="NO_TOKEN")
        raise ErrorCodeException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=ErrorCode.INVALID_CREDENTIALS,
        )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
    except ExpiredSignatureError:
        raise ErrorCodeException(status_code=401, error_code=ErrorCode.MFA_TOKEN_EXPIRED)
    except JWTError:
        raise ErrorCodeException(status_code=401, error_code=ErrorCode.INVALID_TOKEN)

    token_type = payload.get("type")
    if token_type not in ("access", "mfa_setup"):
        raise ErrorCodeException(status_code=401, error_code=ErrorCode.INVALID_TOKEN)

    user_id = payload.get("sub")
    if not user_id:
        raise ErrorCodeException(status_code=401, error_code=ErrorCode.INVALID_TOKEN)

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or user.deleted_at is not None or not user.is_active:
        raise ErrorCodeException(status_code=401, error_code=ErrorCode.USER_NOT_FOUND)
    return user
