"""Common FastAPI dependencies: current user, role gates."""
from typing import Iterable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .security import decode_access_token
from ..models import User


# tokenUrl points at the OAuth2-compatible form endpoint so Swagger UI's
# "Authorize" popup can submit username/password directly and get a token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login/form")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
    except ValueError:
        raise credentials_exc

    user_id = payload.get("uid")
    if user_id is None:
        raise credentials_exc

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exc
    return user


def require_roles(*allowed: str):
    """Dependency factory: only allow users whose role.name is in `allowed`."""

    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.name not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.name}' is not permitted to access this resource. "
                       f"Allowed roles: {', '.join(allowed)}",
            )
        return current_user

    return _checker


def require_any_role(roles: Iterable[str]):
    return require_roles(*roles)
