import pytest

from webutils.email_utils import EmailValidator


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
    "user@.com",  # domain starts with dot
    "user@domain",  # no TLD
    "user@domain.c",  # TLD less than 2 characters
    ".user@example.com",  # local part starts with a dot
    "user.@example.com",  # local part ends with a dot
    "user@-example.com",  # the domain starts with a hyphen
    "user@example..com",  # double dot in domain
])
def test_validate_strict_invalid(email_utils):
    """Strict validation should reject addresses violating any regex rule."""
    validator = EmailValidator(email_utils)
    assert not validator.validate_strict()


def test_strict_implies_loose():
    """Any email that passes the hard test should pass the soft test."""
    samples = [
        "user@example.com",
        "user.name+tag+sorting@example.co.uk",
        "user_name@mail.domain.com",
    ]
    for email_utils in samples:
        v = EmailValidator(email_utils)
        assert v.validate_strict()
        assert v.validate_loose()
