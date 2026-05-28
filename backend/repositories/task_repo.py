"""
Repository module for managing Task entities in the database.
This module defines the TaskRepository class, which provides methods for performing CRUD operations on Task entities using SQLAlchemy ORM.
"""

import uuid

from sqlalchemy.orm import Session

from backend.models.task_model import Task as TaskModel
from backend.exceptions.custom_exceptions import TaskNotFoundException, DatabaseOperationException

class TaskRepository:
    """Repository class for managing Task entities in the database."""

    def __init__(self, db_session: Session) -> None:
        """Initialize the TaskRepository with a database session."""

        self.db_session = db_session

    # ------------------------------ CRUD operations ------------------------------

    # ------------------------------ Read operations ------------------------------

    def get_all(self, user_id: uuid.UUID) -> list[TaskModel]:
        """Retrieve all tasks for a given user ID."""
        
        try:
            return self.db_session.query(TaskModel).filter(TaskModel.user_id == user_id).all()
        except Exception as e:
            raise DatabaseOperationException(f"Error retrieving tasks for user ID {user_id}: {str(e)}") from e
    
    def get_by_id(self, task_id: uuid.UUID, user_id: uuid.UUID) -> TaskModel:
        """Retrieve a task by its ID."""
        
        try:
            task: TaskModel | None = self.db_session.query(TaskModel) \
                                        .filter(TaskModel.id == task_id, TaskModel.user_id == user_id) \
                                        .first()
            if not task:
                raise TaskNotFoundException(task_id)
            return task
        except TaskNotFoundException:
            raise
        except Exception as e:
            raise DatabaseOperationException(f"Error retrieving task with ID {task_id}: {str(e)}") from e

    # ------------------------------ Write operations ------------------------------
    
    def create(self, task: TaskModel) -> TaskModel:
        """Create a new task in the database."""

        try:
            self.db_session.add(task)
            self.db_session.commit()
            self.db_session.refresh(task)
            return task
        except Exception as e:
            self.db_session.rollback()
            raise DatabaseOperationException(f"Error creating task: {str(e)}") from e

    def update(self, task: TaskModel) -> TaskModel:
        """Update an existing task in the database."""
        
        try:
            # merged_task = self.db_session.merge(task)
            self.db_session.commit()
            # self.db_session.refresh(merged_task)
            # return merged_task
            self.db_session.refresh(task)
            return task
        except Exception as e:
            self.db_session.rollback()
            raise DatabaseOperationException(f"Error updating task with ID {task.id}: {str(e)}") from e

    def delete(self, task: TaskModel) -> None:
        """Delete a task from the database."""

        try:
            self.db_session.delete(task)
            self.db_session.commit()
        except Exception as e:
            self.db_session.rollback()
            raise DatabaseOperationException(f"Error deleting task with ID {task.id}: {str(e)}") from e