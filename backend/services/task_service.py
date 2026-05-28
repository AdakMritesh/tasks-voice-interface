"""
TaskServices class that provides business logic for task management operations.
This module defines the TaskServices class, which interacts with the TaskRepository to perform CRUD operations on Task entities. The TaskServices class also handles the conversion of TaskModel instances to TaskResponse schemas for API responses.
"""

import uuid

from backend.models.task_model import Task as TaskModel
from backend.schema.task_schema import TaskCreate, TaskUpdate, TaskResponse
from backend.repositories.task_repo import TaskRepository
from backend.utils import convert_task_model_to_response_dto, convert_task_models_to_responses_dto
from backend.exceptions.custom_exceptions import TaskNotFoundException, DatabaseOperationException, ServiceException

class TaskServices:
    def __init__(self, repository: TaskRepository) -> None:
        """Initialize the TaskServices with a TaskRepository instance."""
        
        self.repository = repository

    def get_all(self, user_id: uuid.UUID) -> list[TaskResponse]:
        """Service for retrieving all tasks for a given user ID."""

        try:
            queried_tasks: list[TaskModel] =  self.repository.get_all(user_id)
            if not queried_tasks:
                return []
            return convert_task_models_to_responses_dto(queried_tasks)
        except DatabaseOperationException:
            raise
        except Exception as e:
            raise ServiceException(f"Error retrieving tasks for user ID {user_id}: {str(e)}") from e


    def create(self, task: TaskCreate, user_id: uuid.UUID) -> TaskResponse:
        """Service for creating a new task in the database."""
        
        # TODO: 
        # 1. Add validation to ensure that the user_id exists in the database before creating a task.
        # 2. Add validation for due date to ensure that it is not set to a past date.

        new_task_data: dict[str, object] = task.model_dump(exclude_unset=True)
        new_task_data['user_id'] = user_id
        new_task: TaskModel = TaskModel(**new_task_data)

        try:
            created_task: TaskModel = self.repository.create(new_task)
            return convert_task_model_to_response_dto(created_task)
        except DatabaseOperationException:
            raise
        except Exception as e:
            raise ServiceException(f"Error creating task for user ID {user_id}: {str(e)}") from e


    def update(self, task_id: uuid.UUID, user_id: uuid.UUID, task: TaskUpdate) -> TaskResponse:
        """Service for updating an existing task in the database."""

        try:
            existing_task: TaskModel = self.repository.get_by_id(task_id, user_id)
        except TaskNotFoundException:
            raise
        except DatabaseOperationException:
            raise

        updated_task_data: dict[str, object] = task.model_dump(exclude_unset=True)
        for key, value in updated_task_data.items():
            setattr(existing_task, key, value)
        
        try:
            updated_task: TaskModel = self.repository.update(existing_task)
            return convert_task_model_to_response_dto(updated_task)
        except DatabaseOperationException:
            raise
        except Exception as e:
            raise ServiceException(f"Error updating task with ID {task_id}: {str(e)}") from e


    def delete(self, task_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Service for deleting a task from the database."""

        try:
            existing_task: TaskModel = self.repository.get_by_id(task_id, user_id)
        except TaskNotFoundException:
            raise
        except DatabaseOperationException:
            raise

        try:
            self.repository.delete(existing_task)
        except DatabaseOperationException:
            raise
        except Exception as e:
            raise ServiceException(f"Error deleting task with ID {task_id}: {str(e)}") from e