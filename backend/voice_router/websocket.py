"""
WebSocket endpoint for browser voice sessions.
"""

import json
import uuid
from json import JSONDecodeError

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from backend.auth_placeholder import get_current_user_id
from backend.dependencies import get_task_services
from backend.services.task_service import TaskServices
from backend.voice_router.dto import (
    ErrorEvent,
    ErrorPayload,
    client_voice_event_adapter,
)
from backend.voice_router.orchestrator import VoiceOrchestrator
from backend.voice_router.tools import VoiceTaskTools

router: APIRouter = APIRouter(tags=["Voice"])


@router.websocket("/ws/voice")
async def voice_websocket(
    websocket: WebSocket,
    task_services: TaskServices = Depends(get_task_services),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> None:
    await websocket.accept()
    orchestrator = VoiceOrchestrator(VoiceTaskTools(task_services, user_id))

    try:
        while True:
            raw_message = await websocket.receive_text()

            try:
                raw_event = json.loads(raw_message)
            except JSONDecodeError:
                await websocket.send_json(
                    ErrorEvent(payload=ErrorPayload(message="Invalid JSON payload.")).model_dump()
                )
                continue

            try:
                event = client_voice_event_adapter.validate_python(raw_event)
            except ValidationError as exc:
                await websocket.send_json(
                    ErrorEvent(
                        payload=ErrorPayload(message=f"Invalid voice event: {exc.errors()}")
                    ).model_dump()
                )
                continue

            try:
                response = await orchestrator.handle_event(event)
            except Exception:
                response = ErrorEvent(
                    payload=ErrorPayload(message="I couldn't complete that operation")
                )

            if response is not None:
                await websocket.send_json(response.model_dump())
    except WebSocketDisconnect:
        return
