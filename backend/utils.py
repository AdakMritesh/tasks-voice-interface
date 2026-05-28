"""Utility functions"""

from backend.models.task_model import Task as TaskModel
from backend.schema.task_schema import TaskCreate, TaskResponse
from backend.models.user_model import User as UserModel
from backend.schema.user_schema import User as UserDTO

def convert_task_model_to_response_dto(task: TaskModel) -> TaskResponse:
    """Convert TaskModel instance to TaskResponse schema."""

    return TaskResponse.model_validate(task)


def convert_task_models_to_responses_dto(tasks: list[TaskModel]) -> list[TaskResponse]:
    """Convert list of TaskModel instances to list of TaskResponse schemas."""

    return [convert_task_model_to_response_dto(task) for task in tasks]


def convert_user_model_to_user_schema_dto(user: UserModel) -> UserDTO:
    """Convert UserModel instance to UserDTO schema."""

    return UserDTO.model_validate(user)

# TODO: review
def convert_task_schema_dto_to_task_model(task: TaskCreate) -> TaskModel:
    """Convert TaskCreate schema to TaskModel instance."""

    return TaskModel(
        # user_id=task.user_id,
        title=task.title,
        status=task.status,
        due_date=task.due_date if task.due_date else None
    )