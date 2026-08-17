from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.superuser import SuperuserCreate
from app.services.exceptions import ConflictError, NotFoundError, ServiceError, ValidationError


class SuperuserService:
    """Manages platform superuser accounts (not tied to any business)."""

    def __init__(self, db: Session, actor_id: int):
        self.db = db
        self.actor_id = actor_id

    def list_superusers(self) -> list[User]:
        stmt = select(User).where(User.is_superuser.is_(True)).order_by(User.id)
        return list(self.db.scalars(stmt).all())

    def get_superuser(self, user_id: int) -> User:
        user = self.db.get(User, user_id)
        if user is None or not user.is_superuser:
            raise NotFoundError(f"Superuser {user_id} was not found.")
        return user

    def create_superuser(self, payload: SuperuserCreate) -> User:
        existing = self.db.scalar(select(User.id).where(User.email == payload.email))
        if existing is not None:
            raise ConflictError(f"A user with email '{payload.email}' already exists.")

        user = User(
            business_id=None,
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            role=None,
            is_superuser=True,
            is_active=True,
        )
        self.db.add(user)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Superuser could not be created due to a data conflict.") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while creating superuser.") from exc

        self.db.refresh(user)
        return user

    def set_active_status(self, user_id: int, is_active: bool) -> User:
        user = self.get_superuser(user_id)

        if not is_active and user.id == self.actor_id:
            raise ValidationError("You cannot deactivate your own account.")

        user.is_active = is_active

        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while updating superuser status.") from exc

        self.db.refresh(user)
        return user
