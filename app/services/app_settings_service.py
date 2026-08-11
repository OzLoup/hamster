from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings as app_config
from app.models.app_settings import AppSettings
from app.schemas.app_settings import AppSettingsUpdate
from app.services.exceptions import ServiceError

SETTINGS_ROW_ID = 1


class AppSettingsService:
    """Reads and updates the singleton row of tenant-wide settings."""

    def __init__(self, db: Session):
        self.db = db

    def get_settings(self) -> AppSettings:
        settings_row = self.db.get(AppSettings, SETTINGS_ROW_ID)
        if settings_row is not None:
            return settings_row

        settings_row = AppSettings(id=SETTINGS_ROW_ID, business_name=app_config.app_name)
        self.db.add(settings_row)
        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while initializing settings.") from exc
        self.db.refresh(settings_row)
        return settings_row

    def update_settings(self, payload: AppSettingsUpdate) -> AppSettings:
        settings_row = self.get_settings()
        settings_row.business_name = payload.business_name

        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while updating settings.") from exc

        self.db.refresh(settings_row)
        return settings_row
