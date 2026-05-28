"""
UserService class that provides business logic for user management operations.
This module defines the UserService class, which interacts with the UserRepository to perform CRUD operations on User entities. The UserService class also handles the conversion of UserModel instances to UserSchemas for API responses.
"""
# import uuid

from backend.exceptions.custom_exceptions import ServiceException, UserNotFoundException, DatabaseOperationException
from backend.schema.user_schema import User as UserDTO
from backend.models.user_model import User as UserModel
from backend.repositories.user_repo import UserRepository
from backend.utils import convert_user_model_to_user_schema_dto

class UserService:
    def __init__(self, repository: UserRepository) -> None:
        """Initialize the UserService with a UserRepository instance."""
        
        self.repository = repository

    def get_user(self, username: str) -> UserDTO:
        """Service for retrieving a user by their username."""

        try:
            user = self.repository.get_by_username(username)
            return convert_user_model_to_user_schema_dto(user)
        except UserNotFoundException:
            raise
        except DatabaseOperationException:
            raise
        except Exception as e:
            raise ServiceException(f"Error retrieving user with username {username}: {str(e)}") from e

    def create(self, user: UserDTO) -> UserDTO:
        """Service for creating a new user in the database."""

        new_user_data = user.model_dump(exclude_unset=True)
        new_user = UserModel(**new_user_data)

        try:
            created_user = self.repository.create(new_user)
            return convert_user_model_to_user_schema_dto(created_user)
        except DatabaseOperationException:
            raise
        except Exception as e:
            raise ServiceException(f"Error creating user with username {user.username}: {str(e)}") from e