from typing import Optional

from fastapi import Header, HTTPException, status

from app.config import settings


def verify_setup_token(
    x_setup_token: Optional[str] = Header(None, alias="X-Setup-Token"),
) -> None:
    """Require setup token for mutating setup endpoints when configured."""
    if not settings.SETUP_TOKEN:
        return
    if x_setup_token != settings.SETUP_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing setup token",
        )
