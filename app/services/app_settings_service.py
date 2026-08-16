from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.business import Business
from app.schemas.app_settings import AppSettingsUpdate
from app.services.exceptions import NotFoundError, ServiceError


class AppSettingsService:
    """Reads and updates the calling business's own display name (backed by Business.name)."""

    def __init__(self, db: Session, business_id: int):
        self.db = db
        self.business_id = business_id

    def get_settings(self) -> Business:
        business = self.db.get(Business, self.business_id)
        if business is None:
            raise NotFoundError(f"Business {self.business_id} was not found.")
        return business

    def update_settings(self, payload: AppSettingsUpdate) -> Business:
        business = self.get_settings()
        business.name = payload.business_name

        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while updating settings.") from exc

        self.db.refresh(business)
        return business
