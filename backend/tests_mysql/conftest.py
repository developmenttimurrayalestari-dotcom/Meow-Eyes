"""Keep customer email delivery disabled in the isolated SQL test suite."""
import pytest


@pytest.fixture(autouse=True)
def no_live_verification_email(monkeypatch):
    monkeypatch.setenv('SMTP_HOST', '')
    monkeypatch.setenv('SMTP_PASSWORD', '')
