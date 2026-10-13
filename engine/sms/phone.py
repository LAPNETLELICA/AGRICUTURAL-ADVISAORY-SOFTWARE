"""Cameroon telephone number normalization for outbound SMS."""

import re

_SEPARATORS = re.compile(r"[\s().-]+")
_CAMEROON_LOCAL_NUMBER = re.compile(r"^[26]\d{8}$")


def normalize_cameroon_phone(value: str) -> str:
    """Return a canonical E.164 Cameroon number or raise ``ValueError``."""
    normalized = _SEPARATORS.sub("", value.strip())
    if normalized.startswith("+"):
        normalized = normalized[1:]
    if normalized.startswith("237"):
        normalized = normalized[3:]
    if not _CAMEROON_LOCAL_NUMBER.fullmatch(normalized):
        raise ValueError("a valid Cameroon phone number is required")
    return f"+237{normalized}"
