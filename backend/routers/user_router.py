"""
User management API endpoints for retrieving and creating users.
"""

from fastapi import APIRouter, Depends, status, HTTPException

from backend.exceptions.custom_exceptions import UserNotFoundException, DatabaseOperationException, ServiceException
from backend.services.user_service import UserService
from backend.schema.user_schema import User
from backend.dependencies import get_user_services

router: APIRouter = APIRouter(prefix="/users", tags=["Users"])


@router.get(
        "/{username}",
        response_model=User,
        status_code=status.HTTP_200_OK)
def get_user(
    username: str,
    user_services: UserService = Depends(get_user_services)
    ) -> User:
    """Endpoint to retrieve a user by username."""

    try:
        user: User = user_services.get_user(username)
        return user
    except UserNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except DatabaseOperationException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except ServiceException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while retrieving the user") from e

@router.post(
        "/",
        response_model=User,
        status_code=status.HTTP_201_CREATED
    )
def create_user(
    user: User,
    user_services: UserService = Depends(get_user_services)
    ) -> User:
    """Endpoint to create a new user."""

    try:
        return user_services.create(user)
    except DatabaseOperationException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except ServiceException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while creating the user") from e
