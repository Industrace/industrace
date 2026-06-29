"""Tests for setup endpoint protection."""
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.services.setup_auth import verify_setup_token


def test_verify_setup_token_allows_when_not_configured():
    with patch("app.services.setup_auth.settings") as mock_settings:
        mock_settings.SETUP_TOKEN = ""
        verify_setup_token(x_setup_token=None)


def test_verify_setup_token_rejects_invalid_token():
    with patch("app.services.setup_auth.settings") as mock_settings:
        mock_settings.SETUP_TOKEN = "secret-setup-token"
        with pytest.raises(HTTPException) as exc:
            verify_setup_token(x_setup_token="wrong-token")
        assert exc.value.status_code == 403


def test_verify_setup_token_accepts_valid_token():
    with patch("app.services.setup_auth.settings") as mock_settings:
        mock_settings.SETUP_TOKEN = "secret-setup-token"
        verify_setup_token(x_setup_token="secret-setup-token")
