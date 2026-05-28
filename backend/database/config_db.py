"""
Configuration module for database connection settings.
"""

from typing import Optional
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):

    model_config = SettingsConfigDict(env_file=".env", env_prefix="DB_")

    # Local SQLite database by default. Override with DB_URL if needed.
    url: Optional[str] = "sqlite:///./tasks_voice.sqlite3"

    # Standalone PostgreSQL connection parameters, used only when DB_URL is not set.
    host: str = "localhost"
    port: int = 5432
    username: str = "postgres"
    password: SecretStr = SecretStr("postgres")
    database: str = "psql"

    # SSL configuration
    sslmode: Optional[str] = None
    sslrootcert: Optional[str] = None

    # DB engine configuration
    echo: bool = False
    pool_pre_ping: bool = True
    pool_size: int = 10
    max_overflow: int = 20

    # DB session configuration
    autocommit: bool = False
    autoflush: bool = False


    # TODO: Add logging here to log the loaded settings, ensuring that sensitive information like passwords is not logged. 
    # Adding validation for the settings to ensure they are correct before attempting to connect to the database.
    
    def get_db_url(self) -> str:
        """Constructs the database URL from the settings."""

        if self.url is not None:
            return self.url

        safe_username = quote_plus(self.username)
        safe_password = quote_plus(self.password.get_secret_value())

        return f"postgresql+psycopg2://{safe_username}:{safe_password}@{self.host}:{self.port}/{self.database}"

    def get_conn_args(self) -> dict[str, str]:
        """Constructs the connection arguments from the settings."""

        if self.get_db_url().startswith("sqlite"):
            return {"check_same_thread": False}

        if self.sslmode is None:
            return {}
        elif self.sslmode in ("verify-ca", "verify-full"):
            return {
                "sslmode": self.sslmode,
                "sslrootcert": self.sslrootcert
            }
        else:
            return {
                "sslmode": self.sslmode
            }

settings: Settings = Settings()
