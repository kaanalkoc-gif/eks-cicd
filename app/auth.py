"""
JWT authentication dependencies.
Replaces static API key auth on write endpoints (Step 22).
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_access_token
from app.services import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency that validates a Bearer JWT and returns the current user.
    Raises 401 if the token is missing, invalid, or the user no longer exists.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not isinstance(email, str) or not email:
            raise credentials_exception
    except ValueError:
        raise credentials_exception from None

    user = UserService.get_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user
