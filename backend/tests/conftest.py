"""Shared fixtures for Meow Eyes backend tests."""
import os
import pytest

# These old suites mutate a running server and are never collected implicitly.
# The SQL acceptance suite is selected by pytest-mysql.ini.
LIVE_TESTS = os.environ.get("MEOW_LEGACY_HTTP_TESTS") == "1"
collect_ignore_glob = [] if LIVE_TESTS else ["test_*.py"]
if LIVE_TESTS:
    if not os.environ.get("REACT_APP_BACKEND_URL"):
        raise pytest.UsageError("Set an explicit isolated REACT_APP_BACKEND_URL for legacy HTTP tests")
    import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _login(api_session, email, password):
    r = api_session.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
    return r


@pytest.fixture(scope="session")
def admin_token():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": "admin@meoweyes.id", "password": "Admin@123"})
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="session")
def customer_token():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": "customer@meoweyes.id", "password": "Customer@123"})
    assert r.status_code == 200, f"Customer login failed: {r.text}"
    return r.json()["token"]


@pytest.fixture
def admin_client(admin_token):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {admin_token}"})
    return s


@pytest.fixture
def customer_client(customer_token):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {customer_token}"})
    return s
