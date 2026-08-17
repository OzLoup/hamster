from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.business import Business
from app.models.user import User
from app.schemas.business import BusinessCreateWithAdmin
from app.services.exceptions import ConflictError, NotFoundError, ServiceError


class BusinessAdminService:
    """Superuser-only: provisions and manages tenants (businesses) across the whole platform."""

    def __init__(self, db: Session):
        self.db = db

    def list_businesses(self) -> list[Business]:
        stmt = select(Business).order_by(Business.id)
        return list(self.db.scalars(stmt).all())

    def get_business(self, business_id: int) -> Business:
        business = self.db.get(Business, business_id)
        if business is None:
            raise NotFoundError(f"Business {business_id} was not found.")
        return business

    def create_business(self, payload: BusinessCreateWithAdmin) -> Business:
        existing_email = self.db.scalar(select(User.id).where(User.email == payload.admin_email))
        if existing_email is not None:
            raise ConflictError(f"A user with email '{payload.admin_email}' already exists.")

        business = Business(name=payload.business_name, is_active=True)
        self.db.add(business)
        self.db.flush()

        admin = User(
            business_id=business.id,
            email=payload.admin_email,
            hashed_password=hash_password(payload.admin_password),
            full_name=payload.admin_full_name,
            role="admin",
            is_superuser=False,
            is_active=True,
        )
        self.db.add(admin)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Business could not be created due to a data conflict.") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while creating business.") from exc

        self.db.refresh(business)
        return business

    def set_active_status(self, business_id: int, is_active: bool) -> Business:
        business = self.get_business(business_id)
        business.is_active = is_active

        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while updating business status.") from exc

        self.db.refresh(business)
        return business
