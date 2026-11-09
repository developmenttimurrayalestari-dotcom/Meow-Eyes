"""Validated MySQL settings, independent of the existing MongoDB environment."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
import ssl
from typing import Mapping

from dotenv import dotenv_values, load_dotenv
from sqlalchemy.engine import URL


DEFAULT_ENV_FILE = Path(__file__).resolve().parent.parent / ".env.mysql"
STRICT_SQL_MODE = (
    "STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION,"
    "ONLY_FULL_GROUP_BY,NO_ZERO_DATE,NO_ZERO_IN_DATE"
)


def load_runtime_environment(env_file: Path = DEFAULT_ENV_FILE) -> None:
    """Load app flags and secrets literally, honoring explicit process variables.

    Keep the same no-interpolation policy as MySQLSettings. Otherwise a password
    containing ${NAME} would be changed before the settings reader can see it.
    """
    load_dotenv(env_file, override=False, interpolate=False)


class ConfigurationError(ValueError):
    """Invalid configuration; messages contain names, never secret values."""


def _integer(values: Mapping[str, str], name: str, default: int) -> int:
    try:
        return int(values.get(name, str(default)))
    except (TypeError, ValueError):
        raise ConfigurationError(f"{name} must be an integer") from None


def _optional_path(value: str | None, base_dir: Path) -> Path | None:
    if not value or not value.strip():
        return None
    path = Path(value.strip()).expanduser()
    return path if path.is_absolute() else (base_dir / path).resolve()


@dataclass(frozen=True, slots=True)
class MySQLSettings:
    host: str
    port: int
    database: str
    username: str
    password: str = field(repr=False)
    app_env: str = "development"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout_seconds: int = 30
    pool_recycle_seconds: int = 1800
    connect_timeout_seconds: int = 5
    read_timeout_seconds: int = 30
    health_timeout_seconds: int = 5
    ssl_mode: str = "disabled"
    ssl_ca: Path | None = None
    ssl_cert: Path | None = None
    ssl_key: Path | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.app_env not in {"development", "test", "production"}:
            raise ConfigurationError("APP_ENV must be development, test, or production")
        if not self.host or any(c.isspace() for c in self.host) or any(
            c in self.host for c in "/?#@"
        ):
            raise ConfigurationError("MYSQL_HOST must be a hostname or IP address")
        if not re.fullmatch(r"[A-Za-z0-9_]{1,64}", self.database):
            raise ConfigurationError("MYSQL_DATABASE must contain 1-64 letters, digits, or underscores")
        if not self.username or any(ord(c) < 32 for c in self.username):
            raise ConfigurationError("MYSQL_USER must be nonempty and contain no control characters")
        if not self.password or not self.password.strip() or "\x00" in self.password:
            raise ConfigurationError("MYSQL_PASSWORD must be set to a nonempty password")

        limits = (
            ("MYSQL_PORT", self.port, 1, 65535),
            ("MYSQL_POOL_SIZE", self.pool_size, 1, 100),
            ("MYSQL_MAX_OVERFLOW", self.max_overflow, 0, 100),
            ("MYSQL_POOL_TIMEOUT_SECONDS", self.pool_timeout_seconds, 1, 120),
            ("MYSQL_POOL_RECYCLE_SECONDS", self.pool_recycle_seconds, 60, 86400),
            ("MYSQL_CONNECT_TIMEOUT_SECONDS", self.connect_timeout_seconds, 1, 60),
            ("MYSQL_READ_TIMEOUT_SECONDS", self.read_timeout_seconds, 1, 300),
            ("MYSQL_HEALTH_TIMEOUT_SECONDS", self.health_timeout_seconds, 1, 60),
        )
        for name, value, minimum, maximum in limits:
            if not isinstance(value, int) or isinstance(value, bool) or not minimum <= value <= maximum:
                raise ConfigurationError(f"{name} must be an integer between {minimum} and {maximum}")

        if self.ssl_mode not in {"disabled", "verify_identity"}:
            raise ConfigurationError("MYSQL_SSL_MODE must be disabled or verify_identity")
        if self.app_env == "production" and self.ssl_mode != "verify_identity":
            raise ConfigurationError("APP_ENV=production requires MYSQL_SSL_MODE=verify_identity")
        if self.ssl_mode == "disabled" and any((self.ssl_ca, self.ssl_cert, self.ssl_key)):
            raise ConfigurationError("MySQL TLS certificate settings require MYSQL_SSL_MODE=verify_identity")
        if bool(self.ssl_cert) != bool(self.ssl_key):
            raise ConfigurationError("MYSQL_SSL_CERT and MYSQL_SSL_KEY must be configured together")
        for name, value in (
            ("MYSQL_SSL_CA", self.ssl_ca),
            ("MYSQL_SSL_CERT", self.ssl_cert),
            ("MYSQL_SSL_KEY", self.ssl_key),
        ):
            if value is not None and not value.is_file():
                raise ConfigurationError(f"{name} must point to an existing certificate file")

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
        env_file: str | Path | None = DEFAULT_ENV_FILE,
    ) -> "MySQLSettings":
        """Read only .env.mysql; process variables override the optional file.

        Pass env_file=None to use environment variables exclusively. Interpolation
        is disabled so passwords containing '$' or '${...}' remain unchanged.
        Relative TLS file paths resolve against the configured env file's folder.
        """
        values: dict[str, str] = {}
        base_dir = Path.cwd()
        if env_file is not None:
            path = Path(env_file).resolve()
            base_dir = path.parent
            if path.exists():
                try:
                    values.update({k: v for k, v in dotenv_values(path, interpolate=False).items() if v is not None})
                except OSError:
                    raise ConfigurationError("Cannot read the MySQL environment file") from None
        values.update(os.environ if environ is None else environ)

        return cls(
            host=values.get("MYSQL_HOST", "127.0.0.1").strip(),
            port=_integer(values, "MYSQL_PORT", 3306),
            database=values.get("MYSQL_DATABASE", "meow_eyes").strip(),
            username=values.get("MYSQL_USER", "meow_app").strip(),
            password=values.get("MYSQL_PASSWORD", ""),
            app_env=values.get("APP_ENV", "development").strip().lower(),
            pool_size=_integer(values, "MYSQL_POOL_SIZE", 5),
            max_overflow=_integer(values, "MYSQL_MAX_OVERFLOW", 10),
            pool_timeout_seconds=_integer(values, "MYSQL_POOL_TIMEOUT_SECONDS", 30),
            pool_recycle_seconds=_integer(values, "MYSQL_POOL_RECYCLE_SECONDS", 1800),
            connect_timeout_seconds=_integer(values, "MYSQL_CONNECT_TIMEOUT_SECONDS", 5),
            read_timeout_seconds=_integer(values, "MYSQL_READ_TIMEOUT_SECONDS", 30),
            health_timeout_seconds=_integer(values, "MYSQL_HEALTH_TIMEOUT_SECONDS", 5),
            ssl_mode=values.get("MYSQL_SSL_MODE", "disabled").strip().lower(),
            ssl_ca=_optional_path(values.get("MYSQL_SSL_CA"), base_dir),
            ssl_cert=_optional_path(values.get("MYSQL_SSL_CERT"), base_dir),
            ssl_key=_optional_path(values.get("MYSQL_SSL_KEY"), base_dir),
        )

    @property
    def sqlalchemy_url(self) -> URL:
        """Keep credentials structured, including passwords with URL characters."""
        return URL.create(
            "mysql+asyncmy",
            username=self.username,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
            query={"charset": "utf8mb4"},
        )

    def connect_args(self) -> dict:
        """Driver options; callers must not log the returned values."""
        args: dict = {
            "connect_timeout": self.connect_timeout_seconds,
            "read_timeout": self.read_timeout_seconds,
            # asyncmy's sql_mode kwarg is inserted into SQL without quoting.
            # Set session values with a fixed, quoted initialization SQL
            # statement instead. STRICT_SQL_MODE is code, never user input.
            "init_command": (
                "SET SESSION time_zone = '+00:00', "
                f"sql_mode = '{STRICT_SQL_MODE}', innodb_strict_mode = ON"
            ),
            "local_infile": False,
        }
        if self.ssl_mode == "verify_identity":
            try:
                context = ssl.create_default_context(
                    cafile=str(self.ssl_ca) if self.ssl_ca else None
                )
                context.check_hostname = True
                context.verify_mode = ssl.CERT_REQUIRED
                if self.ssl_cert and self.ssl_key:
                    context.load_cert_chain(str(self.ssl_cert), str(self.ssl_key))
            except (ssl.SSLError, OSError):
                raise ConfigurationError("Cannot configure MySQL TLS; check certificate files") from None
            args["ssl"] = context
        return args
