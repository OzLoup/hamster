from app.core.security import create_session_token, hash_password, read_session_token, verify_password


def test_hash_password_produces_a_salted_hash_different_from_the_input():
    # Act
    hashed = hash_password("Password123")

    # Assert
    assert hashed != "Password123"
    assert hashed.startswith("$2b$")


def test_hash_password_is_salted_so_repeated_calls_differ():
    # Act
    first = hash_password("Password123")
    second = hash_password("Password123")

    # Assert
    assert first != second


def test_verify_password_returns_true_for_matching_password():
    # Arrange
    hashed = hash_password("Password123")

    # Act / Assert
    assert verify_password("Password123", hashed) is True


def test_verify_password_returns_false_for_wrong_password():
    # Arrange
    hashed = hash_password("Password123")

    # Act / Assert
    assert verify_password("WrongPassword", hashed) is False


def test_session_token_roundtrip_returns_the_same_user_id():
    # Arrange
    token = create_session_token(42)

    # Act
    user_id = read_session_token(token, max_age_seconds=3600)

    # Assert
    assert user_id == 42


def test_read_session_token_rejects_a_tampered_token():
    # Arrange
    token = create_session_token(42)
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

    # Act / Assert
    assert read_session_token(tampered, max_age_seconds=3600) is None


def test_read_session_token_rejects_garbage_input():
    # Act / Assert
    assert read_session_token("not-a-real-token", max_age_seconds=3600) is None


def test_read_session_token_rejects_an_expired_token():
    # Arrange
    token = create_session_token(42)

    # Act / Assert
    assert read_session_token(token, max_age_seconds=-1) is None
