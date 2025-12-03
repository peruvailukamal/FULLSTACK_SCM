import pytest
from pydantic import ValidationError
from backend.models.user import UserSchema


def test_password_too_short():
    with pytest.raises(ValidationError):
        UserSchema(username="u1", email="test@example.com", password="A1@a")


def test_password_missing_uppercase():
    with pytest.raises(ValidationError):
        UserSchema(username="u1", email="test@example.com", password="abcdefg1@")


def test_password_missing_digit():
    with pytest.raises(ValidationError):
        UserSchema(username="u1", email="test@example.com", password="Abcdefg@")


def test_password_missing_special():
    with pytest.raises(ValidationError):
        UserSchema(username="u1", email="test@example.com", password="Abcdefg1")


def test_valid_password_and_email():
    u = UserSchema(username="user", email="ok@example.com", password="StrongP@ss1")
    assert u.email == "ok@example.com"
    assert u.username == "user"
