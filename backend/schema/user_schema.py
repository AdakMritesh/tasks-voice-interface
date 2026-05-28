"""
Schema definitions for user-related operations
"""

import uuid

from pydantic import BaseModel, Field, AliasChoices, ConfigDict

class User(BaseModel):

    id: uuid.UUID

    username: str = Field(
        validation_alias=AliasChoices(
            'username',
            'userId',
            'userName',
            'user_id',
            'user_name'
        )
    )
    
    display_name: str = Field(
        validation_alias=AliasChoices(
            'display_name',
            'displayName',
            'name'
        )
    )
    
    model_config = ConfigDict(from_attributes=True)
