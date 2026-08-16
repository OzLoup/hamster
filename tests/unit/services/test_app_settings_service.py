from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models.business import Business
from app.schemas.app_settings import AppSettingsUpdate
from app.services.app_settings_service import AppSettingsService
from app.services.exceptions import NotFoundError, ServiceError


@pytest.fixture()
def service(db_session, business):
    return AppSettingsService(db_session, business.id)


def test_get_settings_returns_this_business(service, business):
    # Act
    settings_row = service.get_settings()

    # Assert
    assert settings_row.id == business.id
    assert settings_row.name == business.name


def test_get_settings_missing_business_raises_not_found(db_session):
    # Arrange
    service = AppSettingsService(db_session, business_id=999)

    # Act / Assert
    with pytest.raises(NotFoundError, match="Business 999 was not found"):
        service.get_settings()


def test_update_settings_changes_business_name(service):
    # Arrange
    payload = AppSettingsUpdate(business_name="Ferretería El Tornillo")

    # Act
    updated = service.update_settings(payload)

    # Assert
    assert updated.name == "Ferretería El Tornillo"


def test_update_settings_persists_across_reads(service):
    # Arrange
    service.update_settings(AppSettingsUpdate(business_name="Panadería Central"))

    # Act
    reread = service.get_settings()

    # Assert
    assert reread.name == "Panadería Central"


def test_update_settings_does_not_affect_other_businesses(service, db_session):
    # Arrange
    other = Business(name="Other Business")
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)
    other_service = AppSettingsService(db_session, other.id)

    # Act
    service.update_settings(AppSettingsUpdate(business_name="Renamed"))

    # Assert
    assert other_service.get_settings().name == "Other Business"


def test_update_settings_sqlalchemy_error_raises_service_error_and_rolls_back():
    # Arrange
    existing = Business(id=1, name="Hamster")

    db = MagicMock()
    db.get.return_value = existing
    db.commit.side_effect = SQLAlchemyError("db down")

    service = AppSettingsService(db, business_id=1)
    payload = AppSettingsUpdate(business_name="New Name")

    # Act / Assert
    with pytest.raises(ServiceError, match="Unexpected database error while updating settings"):
        service.update_settings(payload)
    db.rollback.assert_called_once()
