"""
In-memory voice session state for a single websocket connection.
"""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel


class PendingDeleteConfirmation(BaseModel):
    type: Literal["delete_task"] = "delete_task"
    query: str
    candidate_task_ids: list[str]


@dataclass
class VoiceSessionMemory:
    session_id: str
    last_referenced_task_ids: list[str] = field(default_factory=list)
    pending_confirmation: PendingDeleteConfirmation | None = None
    recent_transcript_history: list[str] = field(default_factory=list)

    def remember_task_ids(self, task_ids: list[str]) -> None:
        self.last_referenced_task_ids = task_ids

    def set_pending_delete(self, query: str, candidate_task_ids: list[str]) -> None:
        self.pending_confirmation = PendingDeleteConfirmation(
            query=query,
            candidate_task_ids=candidate_task_ids,
        )
        self.remember_task_ids(candidate_task_ids)

    def clear_pending_confirmation(self) -> None:
        self.pending_confirmation = None
