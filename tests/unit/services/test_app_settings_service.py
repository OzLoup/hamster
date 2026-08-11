from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings as app_config
from app.models.app_settings import AppSettings
from app.schemas.app_settings import AppSettingsUpdate
from app.services.app_settings_service import AppSettingsService
from app.services.exceptions import ServiceError


@pytest.fixture()
def service(db_session):
    return AppSettingsService(db_session)


def test_get_settings_creates_default_row_when_missing(service):
    # Act
    settings_row = service.get_settings()

    # Assert
    assert settings_row.id == 1
    assert settings_row.business_name == app_config.app_name


def test_get_settings_returns_existing_row_without_duplicating(service, db_session):
    # Arrange
    first = service.get_settings()

    # Act
    second = service.get_settings()

    # Assert
    assert second.id == first.id
    count = db_session.query(AppSettings).count()
    assert count == 1


def test_update_settings_changes_business_name(service):
    # Arrange
    service.get_settings()
    payload = AppSettingsUpdate(business_name="Ferretería El Tornillo")

    # Act
    updated = service.update_settings(payload)

    # Assert
    assert updated.business_name == "Ferretería El Tornillo"


def test_update_settings_persists_across_reads(service):
    # Arrange
    service.update_settings(AppSettingsUpdate(business_name="Panadería Central"))

    # Act
    reread = service.get_settings()

    # Assert
    assert reread.business_name == "Panadería Central"


def test_get_settings_sqlalchemy_error_raises_service_error_and_rolls_back():
    # Arrange
    db = MagicMock()
    db.get.return_value = None
    db.commit.side_effect = SQLAlchemyError("db down")

    service = AppSettingsService(db)

    # Act / Assert
    with pytest.raises(ServiceError, match="Unexpected database error while initializing settings"):
        service.get_settings()
    db.rollback.assert_called_once()


def test_update_settings_sqlalchemy_error_raises_service_error_and_rolls_back():
    # Arrange
    existing = AppSettings(id=1, business_name="Hamster")

    db = MagicMock()
    db.get.return_value = existing
    db.commit.side_effect = SQLAlchemyError("db down")

    service = AppSettingsService(db)
    payload = AppSettingsUpdate(business_name="New Name")

    # Act / Assert
    with pytest.raises(ServiceError, match="Unexpected database error while updating settings"):
        service.update_settings(payload)
    db.rollback.assert_called_once()
