from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.exceptions import AuthorizationError, ConflictError, NotFoundError, ServiceError, ValidationError


class UserService:
    """Manages the users of a single business. Only admins may touch other admin accounts."""

    def __init__(self, db: Session, business_id: int, actor_id: int, actor_role: str | None):
        self.db = db
        self.business_id = business_id
        self.actor_id = actor_id
        self.actor_role = actor_role

    def list_users(self) -> list[User]:
        stmt = select(User).where(User.business_id == self.business_id).order_by(User.id)
        return list(self.db.scalars(stmt).all())

    def get_user(self, user_id: int) -> User:
        user = self.db.get(User, user_id)
        if user is None or user.business_id != self.business_id:
            raise NotFoundError(f"User {user_id} was not found.")
        return user

    def create_user(self, payload: UserCreate) -> User:
        if payload.role == "admin" and self.actor_role != "admin":
            raise AuthorizationError("Only an administrator can create another administrator account.")

        self._ensure_unique_email(payload.email)

        user = User(
            business_id=self.business_id,
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            role=payload.role,
            is_superuser=False,
            is_active=True,
        )
        self.db.add(user)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("User could not be created due to a data conflict.") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while creating user.") from exc

        self.db.refresh(user)
        return user

    def update_user(self, user_id: int, payload: UserUpdate) -> User:
        user = self.get_user(user_id)
        self._ensure_can_manage(user)

        updates = payload.model_dump(exclude_unset=True)

        if "role" in updates and updates["role"] == "admin" and self.actor_role != "admin":
            raise AuthorizationError("Only an administrator can promote a user to administrator.")

        if "email" in updates and updates["email"] != user.email:
            self._ensure_unique_email(updates["email"])

        password = updates.pop("password", None)
        if password:
            user.hashed_password = hash_password(password)

        for field, value in updates.items():
            setattr(user, field, value)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("User could not be updated due to a data conflict.") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while updating user.") from exc

        self.db.refresh(user)
        return user

    def set_active_status(self, user_id: int, is_active: bool) -> User:
        user = self.get_user(user_id)
        self._ensure_can_manage(user)

        if not is_active and user.id == self.actor_id:
            raise ValidationError("You cannot deactivate your own account.")

        user.is_active = is_active

        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while updating user status.") from exc

        self.db.refresh(user)
        return user

    def _ensure_can_manage(self, user: User) -> None:
        if user.role == "admin" and self.actor_role != "admin":
            raise AuthorizationError("Only an administrator can manage another administrator account.")

    def _ensure_unique_email(self, email: str) -> None:
        existing = self.db.scalar(select(User.id).where(User.email == email))
        if existing is not None:
            raise ConflictError(f"A user with email '{email}' already exists.")
