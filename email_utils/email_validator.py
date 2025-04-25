import re
from typing import Pattern


class EmailValidator:
    """
    A simple email_utils validation class supporting two modes:
    - Loose validation: basic structural checks
    - Strict validation: full regex-based validation
    """

    # Precompile strict validation regex for better performance
    _STRICT_PATTERN: Pattern = re.compile(
        r"""
        ^(?!\.)                  # local part must not start with a dot
        [A-Za-z0-9._%+-]+        # allowed characters in local part
        (?<!\.)                  # local part must not end with a dot
        @
        (?!-)                    # domain must not start with a hyphen
        [A-Za-z0-9-]+            # allowed characters in domain labels
        (?:\.[A-Za-z0-9-]+)*     # additional domain labels
        \.[A-Za-z]{2,}$          # top-level domain with at least 2 letters
        """,
        re.VERBOSE,
    )

    def __init__(self, email: str) -> None:
        """
        Initialize with an email_utils address.
        Leading/trailing whitespace is stripped.
        """
        self.email: str = email.strip()

    def validate_loose(self) -> bool:
        """
        Perform loose validation of the email_utils address.

        Checks:
          - presence of '@'
          - non-empty local part
          - domain contains at least one dot
          - domain does not start with a dot
        """
        if "@" not in self.email:
            return False

        local_part, _, domain = self.email.partition("@")
        if not local_part:
            return False

        if domain.startswith("."):
            return False

        return "." in domain

    def validate_strict(self) -> bool:
        """
        Perform strict validation using a precompiled regex.

        The regex enforces:
          - allowed characters in local and domain parts
          - local part does not start/end with a dot
          - domain labels do not start with a hyphen
          - top-level domain is at least 2 letters long
        """
        return bool(self._STRICT_PATTERN.match(self.email))
