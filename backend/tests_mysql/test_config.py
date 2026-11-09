"""Configuration and health contracts, without contacting any database server."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from hashlib import sha1
import re
import ssl

import asyncmy
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

from mysql.config import ConfigurationError, MySQLSettings
from mysql.database import (
    Database, ReadinessResult, EXPECTED_SCHEMA_REVISION,
    supported_mysql_version, innodb_compatibility,
)
import mysql_bootstrap


def settings(**overrides: str) -> MySQLSettings:
    values = {
        "MYSQL_HOST": "127.0.0.1",
        "MYSQL_PORT": "3307",
        "MYSQL_DATABASE": "meow_test",
        "MYSQL_USER": "test_app",
        "MYSQL_PASSWORD": "test-only-password",
        "APP_ENV": "test",
    }
    values.update(overrides)
    return MySQLSettings.from_env(environ=values, env_file=None)


def test_password_special_characters_round_trip_without_being_logged():
    password = "pa@ss:/#%?word${literal}+ value"
    config = settings(MYSQL_PASSWORD=password)
    url = config.sqlalchemy_url
    assert make_url(url.render_as_string(hide_password=False)).password == password
    assert url.database == "meow_test"
    assert url.query["charset"] == "utf8mb4"
    assert password not in repr(config)
    assert password not in str(url)
    assert "***" in str(url)


def test_environment_overrides_file_and_dollar_password_stays_literal(tmp_path):
    env_file = tmp_path / ".env.mysql"
    env_file.write_text(
        'MYSQL_PASSWORD="value${UNSET_FOR_TEST}#suffix"\n'
        'MYSQL_HOST=file-host\nMYSQL_PORT=3309\n',
        encoding="utf-8",
    )
    config = MySQLSettings.from_env(environ={"MYSQL_HOST": "process-host"}, env_file=env_file)
    assert config.host == "process-host"
    assert config.port == 3309
    assert config.password == "value${UNSET_FOR_TEST}#suffix"


def test_legacy_mongo_environment_cannot_configure_mysql():
    with pytest.raises(ConfigurationError, match="MYSQL_PASSWORD"):
        MySQLSettings.from_env(
            environ={"MONGO_URL": "mongodb://unused", "DB_NAME": "legacy"},
            env_file=None,
        )


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("MYSQL_PORT", "zero"),
        ("MYSQL_PORT", "0"),
        ("MYSQL_POOL_SIZE", "0"),
        ("MYSQL_MAX_OVERFLOW", "-1"),
        ("MYSQL_POOL_TIMEOUT_SECONDS", "0"),
        ("MYSQL_POOL_RECYCLE_SECONDS", "10"),
        ("MYSQL_CONNECT_TIMEOUT_SECONDS", "0"),
        ("MYSQL_HEALTH_TIMEOUT_SECONDS", "0"),
        ("MYSQL_PASSWORD", ""),
        ("MYSQL_DATABASE", "bad/name"),
        ("MYSQL_HOST", "mysql://wrong-format"),
        ("MYSQL_SSL_MODE", "required_without_verification"),
        ("APP_ENV", "unknown"),
    ],
)
def test_invalid_settings_fail_early_without_echoing_value(name, value):
    with pytest.raises(ConfigurationError) as error:
        settings(**{name: value})
    assert name in str(error.value)
    assert "test-only-password" not in str(error.value)


def test_production_requires_certificate_and_hostname_verification():
    with pytest.raises(ConfigurationError, match="verify_identity"):
        settings(APP_ENV="production", MYSQL_SSL_MODE="disabled")
    config = settings(APP_ENV="production", MYSQL_SSL_MODE="verify_identity")
    tls = config.connect_args()["ssl"]
    assert isinstance(tls, ssl.SSLContext)
    assert tls.verify_mode == ssl.CERT_REQUIRED
    assert tls.check_hostname is True


def test_partial_tls_client_credentials_are_rejected(tmp_path):
    cert = tmp_path / "client.pem"
    cert.write_text("placeholder", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="configured together"):
        settings(MYSQL_SSL_MODE="verify_identity", MYSQL_SSL_CERT=str(cert))


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("5.7.24-log", True),
        ("5.7.24", True),
        ("5.7.44", True),
        ("5.7.44-enterprise-commercial-advanced-log", True),
        ("5.7.23-log", False),
        ("5.6.51", False),
        ("8.4.0", False),
        ("8.4.7-commercial", False),
        ("9.0.1", False),
        ("8.0.36", False),
        ("10.11.8-MariaDB-0", False),
        ("5.7.24-MariaDB", False),
        ("5.7.24.1", False),
        ("unrecognized", False),
    ],
)
def test_mysql_version_gate(version, expected):
    assert supported_mysql_version(version) is expected


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({}, "server_compatible"),
        ({"large_prefix": "ON", "file_per_table": "ON"}, "server_compatible"),
        ({"page_size": 32768}, "server_compatible"),
        ({"page_size": 65536}, "server_compatible"),
        ({"large_prefix": 0}, "innodb_large_prefix_required"),
        ({"large_prefix": "OFF"}, "innodb_large_prefix_required"),
        # Explicit DYNAMIC is supported in the system tablespace too; these
        # legacy server preferences must not reject an otherwise valid server.
        ({"file_format": "Antelope"}, "server_compatible"),
        ({"file_per_table": 0}, "server_compatible"),
        ({"page_size": 8192}, "innodb_page_size_unsupported"),
        ({"page_size": 4096}, "innodb_page_size_unsupported"),
        ({"page_size": "unknown"}, "innodb_page_size_unsupported"),
    ],
)
def test_innodb_profile_rejects_servers_that_cannot_store_relational_indexes(overrides, reason):
    profile = dict(large_prefix=1, file_format="Barracuda", file_per_table=1, page_size=16384)
    profile.update(overrides)
    result = innodb_compatibility(profile)
    assert result.reason == reason
    assert result.ready is (reason == "server_compatible")


def test_engine_can_be_constructed_without_connecting_or_importing_mongo():
    database = Database(settings())
    assert database.engine.url.drivername == "mysql+asyncmy"
    assert database.engine.sync_engine.hide_parameters is True
    assert database.engine.echo is False
    assert database.engine.sync_engine.dialect._on_connect_isolation_level == "REPEATABLE READ"
    assert database.session_factory.kw["expire_on_commit"] is False
    assert database.session_factory.kw["autoflush"] is False
    asyncio.run(database.dispose())


def test_asyncmy_initialization_quotes_sql_mode_without_contacting_a_server(monkeypatch):
    """Exercise the installed driver's initialization, with transport stubbed.

    asyncmy 0.2.17 interpolates sql_mode verbatim. A bare mode list would be
    invalid SQL even though engine construction and the other unit tests pass.
    """
    statements = []

    class Transport:
        def close(self):
            pass

    class InspectConnection(asyncmy.Connection):
        def _set_keep_alive(self):
            pass

        def _set_nodelay(self, value):
            pass

        async def _get_server_information(self):
            pass

        async def _request_authentication(self):
            pass

        async def query(self, statement, unbuffered=False):
            statements.append(statement)

        async def commit(self):
            pass

        async def autocommit(self, value):
            pass

    async def exercise():
        async def no_network(*args, **kwargs):
            return Transport(), None

        monkeypatch.setattr(asyncio.get_running_loop(), "create_connection", no_network)
        config = settings()
        connection = InspectConnection(
            user=config.username, password=config.password, **config.connect_args()
        )
        try:
            await connection.connect()
        finally:
            connection.close()

    asyncio.run(exercise())
    mode_statements = [statement for statement in statements if "sql_mode" in statement]
    assert len(mode_statements) == 1
    assert re.search(r"sql_mode\s*=\s*'[^']*STRICT_TRANS_TABLES[^']*'", mode_statements[0])
    assert any("time_zone = '+00:00'" in statement for statement in statements)
    assert any("innodb_strict_mode = ON" in statement for statement in statements)


def test_mysql57_native_password_challenge_works_without_a_server():
    """Use the installed driver's default MySQL5.7 authentication algorithm.

    Verify the challenge response by reproducing the server-side comparison
    from its stored double-SHA1 password hash, rather than merely reimplementing
    the client's scramble routine as the assertion.
    """
    from asyncmy.auth import scramble_native_password

    password = b"test-only-native-password"
    challenge = b"0123456789abcdefghij"
    stored_password_hash = sha1(sha1(password).digest()).digest()
    response = scramble_native_password(password, challenge)
    challenge_hash = sha1(challenge + stored_password_hash).digest()
    recovered_first_hash = bytes(left ^ right for left, right in zip(response, challenge_hash))
    assert len(response) == 20
    assert sha1(recovered_first_hash).digest() == stored_password_hash
    assert scramble_native_password(b"", challenge) == b""


def test_optional_sha256_auth_rsa_dependency_works_without_a_server():
    """Keep support for accounts explicitly using MySQL5.7 sha256_password."""
    from asyncmy.auth import sha2_rsa_encrypt
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    password = b"test-only-auth-password"
    salt = b"0123456789abcdefghij"
    encrypted = sha2_rsa_encrypt(password, salt, public_key)
    salted = private_key.decrypt(
        encrypted,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None,
        ),
    )
    restored = bytes(value ^ salt[index % len(salt)] for index, value in enumerate(salted))
    assert restored == password + b"\0"


@pytest.mark.parametrize("ready", [True, False])
def test_bootstrap_reports_schema_only_and_never_mounts_commerce(monkeypatch, ready):
    instances = []

    class FakeDatabase:
        def __init__(self, config):
            self.disposed = False
            instances.append(self)

        async def check_readiness(self):
            return ReadinessResult(ready, "ready" if ready else "schema_revision_mismatch")

        async def dispose(self):
            self.disposed = True

    monkeypatch.setattr(mysql_bootstrap, "Database", FakeDatabase)
    with TestClient(mysql_bootstrap.create_app(settings())) as client:
        live = client.get("/api/health/live")
        assert live.status_code == 200
        response = client.get("/api/health/ready")
        assert response.status_code == (200 if ready else 503)
        assert response.json()["ok"] is ready
        assert response.json()["commerce_routes_enabled"] is False
        assert response.json()["mode"] == "schema_only"
        assert response.json()["database_target"] == "5.7.24-log"
        assert response.json()["expected_schema_revision"] == EXPECTED_SCHEMA_REVISION
        assert client.get("/api/products").status_code == 404
        assert client.post("/api/orders").status_code == 404
    assert instances[0].disposed is True


def test_database_session_rolls_back_on_failure_and_always_closes():
    class FakeSession:
        rolled_back = False
        closed = False

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            self.closed = True

        async def rollback(self):
            self.rolled_back = True

    async def exercise():
        database = Database(settings())
        session = FakeSession()
        database.session_factory = lambda: session
        try:
            with pytest.raises(RuntimeError, match="service failed"):
                async with database.session():
                    raise RuntimeError("service failed")
            assert session.rolled_back is True
            assert session.closed is True
        finally:
            await database.dispose()

    asyncio.run(exercise())


def test_database_dependency_never_commits_a_partial_transaction():
    class FakeSession:
        closed = False
        commits = 0

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            self.closed = True

        async def commit(self):
            self.commits += 1

    async def exercise():
        database = Database(settings())
        session = FakeSession()
        database.session_factory = lambda: session
        try:
            async for yielded in database.session_dependency():
                assert yielded is session
            assert session.closed is True
            assert session.commits == 0
        finally:
            await database.dispose()

    asyncio.run(exercise())


@pytest.mark.parametrize(
    ("version", "revisions", "reason"),
    [
        ("5.7.24-log", [EXPECTED_SCHEMA_REVISION], "ready"),
        ("5.7.44", [EXPECTED_SCHEMA_REVISION], "ready"),
        ("5.7.24-log", [], "schema_revision_mismatch"),
        ("5.7.24-log", ["20261106_0001"], "schema_revision_mismatch"),
        ("5.7.24-log", [EXPECTED_SCHEMA_REVISION, "other_branch"], "schema_revision_mismatch"),
        ("5.7.23-log", [EXPECTED_SCHEMA_REVISION], "unsupported_mysql_version"),
        ("8.0.36", [EXPECTED_SCHEMA_REVISION], "unsupported_mysql_version"),
        ("10.11.8-MariaDB", [EXPECTED_SCHEMA_REVISION], "unsupported_mysql_version"),
    ],
)
def test_readiness_requires_supported_server_and_exact_migration_head(version, revisions, reason):
    class Result:
        def scalar_one(self):
            return version

        def scalars(self):
            return self

        def all(self):
            return revisions

        def mappings(self):
            return self

        def one(self):
            return dict(large_prefix=1, file_format="Barracuda", file_per_table=1, page_size=16384)

    class Connection:
        async def execute(self, statement):
            return Result()

    class Engine:
        @asynccontextmanager
        async def connect(self):
            yield Connection()

    async def exercise():
        database = Database(settings())
        real_engine = database.engine
        database.engine = Engine()
        try:
            result = await database.check_readiness()
            assert result.reason == reason
            assert result.ready is (reason == "ready")
        finally:
            await real_engine.dispose()

    asyncio.run(exercise())


def test_readiness_stops_before_schema_queries_when_storage_profile_is_incompatible():
    statements = []

    class Result:
        def scalar_one(self):
            return "5.7.24-log"

        def mappings(self):
            return self

        def one(self):
            return dict(large_prefix=1, file_format="Barracuda", file_per_table=1, page_size=8192)

    class Connection:
        async def execute(self, statement):
            sql = str(statement)
            statements.append(sql)
            assert sql.startswith("SELECT ")
            assert "alembic_version" not in sql
            return Result()

    class Engine:
        @asynccontextmanager
        async def connect(self):
            yield Connection()

    async def exercise():
        database = Database(settings())
        real_engine = database.engine
        database.engine = Engine()
        try:
            result = await database.check_readiness()
            assert result == ReadinessResult(False, "innodb_page_size_unsupported")
            assert len(statements) == 2
        finally:
            await real_engine.dispose()

    asyncio.run(exercise())


@pytest.mark.parametrize(
    ("code", "reason"),
    [(1146, "schema_not_initialized"), (1045, "database_unavailable")],
)
def test_readiness_redacts_driver_error_details(monkeypatch, caplog, code, reason):
    secret = "private-host secret-account secret-password"

    async def exercise():
        database = Database(settings())

        async def failed_probe():
            raise OperationalError("SELECT private_sql", {}, Exception(code, secret))

        monkeypatch.setattr(database, "_probe", failed_probe)
        try:
            result = await database.check_readiness()
            assert result.ready is False
            assert result.reason == reason
            assert secret not in repr(result)
            assert secret not in caplog.text
            assert "private_sql" not in caplog.text
        finally:
            await database.dispose()

    asyncio.run(exercise())
