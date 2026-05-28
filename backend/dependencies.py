from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.repositories.task_repo import TaskRepository
from backend.repositories.user_repo import UserRepository
from backend.services.task_service import TaskServices
from backend.services.user_service import UserService
from backend.database.initiate_db import Database
from backend.database.config_db import settings

db: Database = Database(settings)

def get_db() -> Generator[Session, None, None]:
    """Dependency function to provide a database session."""
    yield from db.get_db()

def get_task_repository(db: Session = Depends(get_db)) -> TaskRepository:
    """Dependency function to provide a TaskRepository instance."""
    return TaskRepository(db)

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Dependency function to provide a UserRepository instance."""
    return UserRepository(db)

def get_task_services(task_repo: TaskRepository = Depends(get_task_repository)) -> TaskServices:
    """Dependency function to provide a TaskServices instance."""
    return TaskServices(task_repo)

def get_user_services(user_repo: UserRepository = Depends(get_user_repository)) -> UserService:
    """Dependency function to provide a UserService instance."""
    return UserService(user_repo)
