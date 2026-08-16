from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import SESSION_COOKIE_NAME, read_session_token
from app.database.database import get_db
from app.models.user import User


def _resolve_user_from_cookie(request: Request, db: Session) -> User | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    user_id = read_session_token(token, settings.access_token_expire_minutes * 60)
    if user_id is None:
        return None
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        return None
    return user


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """For JSON API routes: 401 if not authenticated."""
    user = _resolve_user_from_cookie(request, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    return user


def get_current_business_id(current_user: User = Depends(get_current_user)) -> int:
    """For JSON API routes scoped to a single business: 403 if the account has no business (superuser)."""
    if current_user.business_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not associated with a business.",
        )
    return current_user.business_id


def require_web_user(request: Request, db: Session = Depends(get_db)) -> User:
    """For HTML page routes: redirects to /login instead of returning a raw 401."""
    user = _resolve_user_from_cookie(request, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": f"/login?next={request.url.path}"},
        )
    return user


def require_business_web_user(current_user: User = Depends(require_web_user)) -> User:
    """For HTML page routes scoped to a business: sends superusers to /admin instead."""
    if current_user.business_id is None:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/admin"})
    return current_user


__all__ = [
    "get_db",
    "get_current_user",
    "get_current_business_id",
    "require_web_user",
    "require_business_web_user",
]
