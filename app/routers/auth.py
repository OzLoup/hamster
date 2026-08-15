from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.security import SESSION_COOKIE_NAME, create_session_token
from app.models.user import User
from app.schemas.auth import CurrentUser, UserLogin
from app.services.auth_service import AuthService
from app.services.dependencies import get_auth_service
from app.services.exceptions import AuthenticationError

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_current_user(user: User) -> CurrentUser:
    return CurrentUser(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_superuser=user.is_superuser,
        business_id=user.business_id,
        business_name=user.business.name if user.business else None,
    )


@router.post("/login", response_model=CurrentUser)
def login(
    payload: UserLogin, response: Response, service: AuthService = Depends(get_auth_service)
) -> CurrentUser:
    try:
        user = service.authenticate(payload.email, payload.password)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    token = create_session_token(user.id)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        samesite="lax",
        secure=settings.app_env != "development",
    )
    return _to_current_user(user)


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"detail": "Logged out."}


@router.get("/me", response_model=CurrentUser)
def me(current_user: User = Depends(get_current_user)) -> CurrentUser:
    return _to_current_user(current_user)
