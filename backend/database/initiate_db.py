"""
This module defines the Database class, which manages the SQLAlchemy engine and session factory for the application. It provides methods to create and cache the engine and session factory, as well as a generator function to yield database sessions for use in request handling.
"""

from typing import Generator

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session, sessionmaker

from .config_db import Settings


class Database:

    def __init__(self, settings: Settings) -> None:
        """Initializes the Database instance with the provided settings."""

        self.settings = settings
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None
        
    # A reivew from claude suggests using thread locking for the engine and session factory creation to ensure thread safety in a multi-threaded environment. This is a good point, especially if the application will be running in a multi-threaded context. Implementing thread locking can

    def get_engine(self) -> Engine:
        """Returns a cached Engine instance. Creates one if it doesn't exist."""

        # TODO: Implement exception handling and logging for database connection issues. Consider retry logic for transient errors.
        if self._engine is None: # Move all these configuration params to a config file.
            engine_kwargs = {
                "echo": self.settings.echo,
                "connect_args": self.settings.get_conn_args(),
            }

            if not self.settings.get_db_url().startswith("sqlite"):
                engine_kwargs.update(
                    {
                        "pool_pre_ping": self.settings.pool_pre_ping,
                        "pool_size": self.settings.pool_size,
                        "max_overflow": self.settings.max_overflow,
                    }
                )

            self._engine = create_engine(
                self.settings.get_db_url(),
                **engine_kwargs
            )
        return self._engine

    # TODO: Implement exception handling and logging for session creation issues.
    def get_session_factory(self) -> sessionmaker[Session]:
        """Returns a cached sessionmaker bound to the engine."""
        
        if self._session_factory is None: # Move all these configuration params to a config file.
            self._session_factory = sessionmaker(
                self.get_engine(),
                autocommit=self.settings.autocommit,
                autoflush=self.settings.autoflush
            )
        return self._session_factory

    # TODO: decide if commit and rollback should be handled here or in the service layer.
    def get_db(self) -> Generator[Session, None, None]: 
        """Generates a new database session for each request. The session is closed after use."""

        db: Session = self.get_session_factory()()
        try:
            yield db
        finally:
            db.close()
