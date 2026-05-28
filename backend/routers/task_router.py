"""
Task management API endpoints for CRUD operations on tasks.
"""

import uuid

from fastapi import APIRouter, Depends, status, HTTPException

from backend.services.task_service import TaskServices
from backend.schema.task_schema import TaskCreate, TaskUpdate, TaskResponse
from backend.auth_placeholder import get_current_user_id
from backend.dependencies import get_task_services
from backend.exceptions.custom_exceptions import DatabaseOperationException, TaskNotFoundException, ServiceException

router: APIRouter = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get(
        "/",
        response_model=list[TaskResponse],
        status_code=status.HTTP_200_OK,
    )
def get_tasks(
    user_id: uuid.UUID = Depends(get_current_user_id),
    task_services: TaskServices = Depends(get_task_services)
    ) -> list[TaskResponse]:
    """Endpoint to retrieve all tasks for a given user ID."""

    try:
        return task_services.get_all(user_id)
    except DatabaseOperationException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except ServiceException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while retrieving tasks") from e


@router.post(
        "/",
        response_model=TaskResponse,
        status_code=status.HTTP_201_CREATED
    )
def create_task(
    task: TaskCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    task_services: TaskServices = Depends(get_task_services)
    ) -> TaskResponse:
    """Endpoint to create a new task."""

    try:
        created_task: TaskResponse = task_services.create(task, user_id)
        return created_task
    except DatabaseOperationException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except ServiceException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while creating the task") from e


@router.patch(
        "/{task_id}",
        response_model=TaskResponse,
        status_code=status.HTTP_200_OK
    )
def update_task(
    task_id: uuid.UUID,
    task: TaskUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    task_services: TaskServices = Depends(get_task_services)
    ) -> TaskResponse:
    """Endpoint to update an existing task."""

    try:
        updated_task: TaskResponse = task_services.update(task_id, user_id, task)
        return updated_task
    except TaskNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with ID {task_id} not found")
    except DatabaseOperationException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except ServiceException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while updating the task") from e

@router.delete(
        "/{task_id}",
        status_code=status.HTTP_204_NO_CONTENT
    )
def delete_task(
    task_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    task_services: TaskServices = Depends(get_task_services)
    ) -> None:
    """Endpoint to delete a task by ID."""
    
    try:
        task_services.delete(task_id, user_id)
    except TaskNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with ID {task_id} not found")
    except DatabaseOperationException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except ServiceException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while deleting the task") from e