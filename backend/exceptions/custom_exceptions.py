"""
Custom exceptions for the Tasks API.
"""

import uuid

class TaskNotFoundException(Exception):
    """Exception raised when a task is not found."""

    def __init__(self, task_id: uuid.UUID) -> None:
        self.task_id = task_id
        self.message = f"Task with ID {task_id} not found."
        super().__init__(self.message)

class UserNotFoundException(Exception):
    """Exception raised when a user is not found."""

    def __init__(self, username: str) -> None:
        self.username = username
        self.message = f"User with username {username} not found."
        super().__init__(self.message)

class ValidationException(Exception):
    """Exception raised for validation errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)

class DatabaseOperationException(Exception):
    """Exception raised for database errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)

class ServiceException(Exception):
    """Exception raised for general service errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)

class UserConflictException(Exception):
    """Exception raised when there is a conflict with an existing user."""

    def __init__(self, username: str) -> None:
        self.username = username
        self.message = f"User with username '{username}' already exists."
        super().__init__(self.message)