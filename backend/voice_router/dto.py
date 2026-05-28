"""
DTOs for the voice websocket protocol.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter


class UserTranscriptPayload(BaseModel):
    text: str


class UserTranscriptEvent(BaseModel):
    type: Literal["USER_TRANSCRIPT"]
    payload: UserTranscriptPayload


class InterruptEvent(BaseModel):
    type: Literal["INTERRUPT"]


class SessionStartEvent(BaseModel):
    type: Literal["SESSION_START"]


ClientVoiceEvent = Annotated[
    UserTranscriptEvent | InterruptEvent | SessionStartEvent,
    Field(discriminator="type"),
]

client_voice_event_adapter = TypeAdapter(ClientVoiceEvent)


class AssistantResponsePayload(BaseModel):
    text: str


class AssistantResponseEvent(BaseModel):
    type: Literal["ASSISTANT_RESPONSE"] = "ASSISTANT_RESPONSE"
    payload: AssistantResponsePayload


class ActionConfirmationRequiredPayload(BaseModel):
    text: str


class ActionConfirmationRequiredEvent(BaseModel):
    type: Literal["ACTION_CONFIRMATION_REQUIRED"] = "ACTION_CONFIRMATION_REQUIRED"
    payload: ActionConfirmationRequiredPayload


class ErrorPayload(BaseModel):
    message: str


class ErrorEvent(BaseModel):
    type: Literal["ERROR"] = "ERROR"
    payload: ErrorPayload
