import pytest
from email_utils import EmailValidator


@pytest.mark.parametrize("email_utils", [
    "user@example.com",
    "user.name+tag+sorting@example.co.uk",
    "user_name@mail.domain.com",
    "user-name@mail-domain.co",
    " uSer@Example.Com ",
])
def test_validate_loose_valid(email_utils):
    """Loose validation should accept well-formed addresses with a dot in the domain."""
    validator = EmailValidator(email_utils)
    assert validator.validate_loose()


@pytest.mark.parametrize("email_utils", [
    "plainaddress",
    "noatsign.com",
    "@nouser.com",
    "user@.com",
    "user@domain",
])
def test_validate_loose_invalid(email_utils):
    """Loose validation should reject addresses without '@' or without a proper domain."""
    validator = EmailValidator(email_utils)
    assert not validator.validate_loose()


@pytest.mark.parametrize("email_utils", [
    "user@example.com",
    "user.name+tag+sorting@example.co.uk",
    "user_name@mail.domain.com",
    "user-name@mail-domain.co",
    "test123@sub.domain.io",
])
def test_validate_strict_valid(email_utils):
    """Strict validation should accept only addresses fully matching the regex."""
    validator = EmailValidator(email_utils)
    assert validator.validate_strict()


@pytest.mark.parametrize("email_utils", [
    "plainaddress",
    "noatsign.com",
    "@nouser.com",
    "user@.com",            # домен начинается с точки
    "user@domain",          # нет TLD
    "user@domain.c",        # TLD менее 2 символов
    ".user@example.com",    # local part начинается с точки
    "user.@example.com",    # local part заканчивается на точку
    "user@-example.com",    # домен начинается с дефиса
    "user@example..com",    # двойная точка в домене
])
def test_validate_strict_invalid(email_utils):
    """Strict validation should reject addresses violating any regex rule."""
    validator = EmailValidator(email_utils)
    assert not validator.validate_strict()


def test_strict_implies_loose():
    """Любой email_utils, прошедший строгую проверку, должен пройти и мягкую."""
    samples = [
        "user@example.com",
        "user.name+tag+sorting@example.co.uk",
        "user_name@mail.domain.com",
    ]
    for email_utils in samples:
        v = EmailValidator(email_utils)
        assert v.validate_strict()
        assert v.validate_loose()
