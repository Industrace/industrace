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
    logger.info(f"Token creato per utente {data.get('sub')} con scadenza {expire}")
    return encoded_jwt


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
    
    return user
