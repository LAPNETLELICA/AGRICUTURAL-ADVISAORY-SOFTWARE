"""Tests for SMS registration value objects."""

import pytest

from engine.sms.phone import normalize_cameroon_phone


def test_normalize_cameroon_phone_accepts_local_and_e164_forms() -> None:
    assert normalize_cameroon_phone("6 77 12 34 56") == "+237677123456"
    assert normalize_cameroon_phone("237677123456") == "+237677123456"


def test_normalize_cameroon_phone_rejects_non_cameroon_number() -> None:
    with pytest.raises(ValueError, match="Cameroon"):
        normalize_cameroon_phone("+447700900123")
