import pytest

from app.schemas.superuser import SuperuserCreate
from app.services.exceptions import ConflictError, NotFoundError, ValidationError
from app.services.superuser_service import SuperuserService
from tests.factories import create_business, create_user


@pytest.fixture()
def actor(db_session):
    return create_user(
        db_session, email="root@hamster.com", role=None, business_id=None, is_superuser=True
    )


@pytest.fixture()
def service(db_session, actor):
    return SuperuserService(db_session, actor.id)


def test_create_superuser_success(service, db_session):
    payload = SuperuserCreate(email="new-root@hamster.com", password="Password123", full_name="New Root")

    # Act
    created = service.create_superuser(payload)

    # Assert
    assert created.id is not None
    assert created.is_superuser is True
    assert created.business_id is None
    assert created.role is None
    assert created.is_active is True


def test_create_superuser_duplicate_email_raises_conflict(service, actor):
    payload = SuperuserCreate(email=actor.email, password="Password123", full_name="Dup")

    # Act / Assert
    with pytest.raises(ConflictError, match="already exists"):
        service.create_superuser(payload)


def test_get_superuser_not_found_for_regular_user(service, db_session):
    business = create_business(db_session, name="A Business")
    regular_user = create_user(db_session, email="regular@biz.com", business_id=business.id, role="admin")

    # Act / Assert
    with pytest.raises(NotFoundError):
        service.get_superuser(regular_user.id)


def test_list_superusers_only_includes_superusers(service, actor, db_session):
    business = create_business(db_session, name="A Business")
    create_user(db_session, email="regular2@biz.com", business_id=business.id, role="admin")
    other_superuser = create_user(
        db_session, email="second-root@hamster.com", role=None, business_id=None, is_superuser=True
    )

    # Act
    superusers = service.list_superusers()

    # Assert
    assert {u.id for u in superusers} == {actor.id, other_superuser.id}


def test_set_active_status_cannot_deactivate_self(service, actor):
    # Act / Assert
    with pytest.raises(ValidationError, match="cannot deactivate your own account"):
        service.set_active_status(actor.id, False)


def test_set_active_status_can_deactivate_another_superuser(service, db_session):
    other_superuser = create_user(
        db_session, email="deactivate-me@hamster.com", role=None, business_id=None, is_superuser=True
    )

    # Act
    deactivated = service.set_active_status(other_superuser.id, False)

    # Assert
    assert deactivated.is_active is False
