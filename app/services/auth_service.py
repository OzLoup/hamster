from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User
from app.services.exceptions import AuthenticationError


class AuthService:
    """Verifies login credentials. Session/cookie handling lives in the router."""

    def __init__(self, db: Session):
        self.db = db

    def authenticate(self, email: str, password: str) -> User:
        user = self.db.scalar(select(User).where(User.email == email))
        if user is None or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password.")
        if not user.is_active:
            raise AuthenticationError("This account has been deactivated.")
        if user.business_id is not None and not user.business.is_active:
            raise AuthenticationError("This business has been deactivated.")
        return user
