"""
Voice orchestrator for LLM routing and deterministic task tools.
"""

import asyncio
import json
import os
import re
import uuid
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from pydantic import BaseModel, Field, ValidationError

from backend.exceptions.custom_exceptions import (
    DatabaseOperationException,
    ServiceException,
    TaskNotFoundException,
)
from backend.voice_router.dto import (
    ActionConfirmationRequiredEvent,
    ActionConfirmationRequiredPayload,
    AssistantResponseEvent,
    AssistantResponsePayload,
    ClientVoiceEvent,
    ErrorEvent,
    ErrorPayload,
    InterruptEvent,
    SessionStartEvent,
    UserTranscriptEvent,
)
from backend.voice_router.prompts import SYSTEM_PROMPT
from backend.voice_router.session_memory import VoiceSessionMemory
from backend.voice_router.tools import (
    AgendaArgs,
    CreateTaskArgs,
    DeleteTaskArgs,
    UpdateTaskArgs,
    VoiceTaskTools,
)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "10"))
LLM_TIMEOUT_MESSAGE = "I'm taking longer than expected. Please try again."
SAFE_OPERATION_FAILURE_MESSAGE = "I couldn't complete that operation"


class OllamaTimeoutError(Exception):
    """Raised when the local Ollama request exceeds the voice timeout budget."""


class AssistantResponseOutput(BaseModel):
    type: str = Field(pattern="^assistant_response$")
    text: str


class ToolCallOutput(BaseModel):
    type: str = Field(pattern="^tool_call$")
    tool: str
    arguments: dict[str, Any]


@dataclass
class ToolCall:
    tool: str
    arguments: CreateTaskArgs | UpdateTaskArgs | DeleteTaskArgs | AgendaArgs


class VoiceOrchestrator:
    def __init__(self, tools: VoiceTaskTools) -> None:
        self.memory = VoiceSessionMemory(session_id=str(uuid.uuid4()))
        self.tools = tools

    async def handle_event(
        self,
        event: ClientVoiceEvent,
    ) -> AssistantResponseEvent | ActionConfirmationRequiredEvent | ErrorEvent | None:
        if isinstance(event, SessionStartEvent):
            return AssistantResponseEvent(
                payload=AssistantResponsePayload(
                    text="I am ready. Tell me what you want to do with your tasks.",
                )
            )

        if isinstance(event, InterruptEvent):
            return None

        if isinstance(event, UserTranscriptEvent):
            text = event.payload.text.strip()

            if not text:
                return ErrorEvent(
                    payload=ErrorPayload(message="Transcript text cannot be empty.")
                )

            self.memory.recent_transcript_history.append(text)
            self.memory.recent_transcript_history = self.memory.recent_transcript_history[-10:]

            pending_response = self._try_handle_pending_confirmation(text)
            if pending_response is not None:
                return pending_response

            return await self._handle_transcript(text)

        return ErrorEvent(payload=ErrorPayload(message="Unsupported voice event."))

    async def _handle_transcript(
        self,
        transcript: str,
    ) -> AssistantResponseEvent | ActionConfirmationRequiredEvent | ErrorEvent:
        try:
            llm_text = await asyncio.to_thread(self._call_ollama, transcript)
        except OllamaTimeoutError:
            return ErrorEvent(payload=ErrorPayload(message=LLM_TIMEOUT_MESSAGE))

        if llm_text is None:
            fallback_response = self._handle_local_fallback(transcript)
            if fallback_response is not None:
                return fallback_response

            return AssistantResponseEvent(
                payload=AssistantResponsePayload(
                    text="I could not reach the local language model. Please try again."
                )
            )

        try:
            parsed = self._parse_llm_output(llm_text)
        except ValidationError:
            return AssistantResponseEvent(
                payload=AssistantResponsePayload(
                    text="I need a little more clarity before changing your tasks."
                )
            )
        except json.JSONDecodeError:
            return AssistantResponseEvent(
                payload=AssistantResponsePayload(
                    text="I had trouble understanding that. Could you say it again?"
                )
            )

        if isinstance(parsed, AssistantResponseOutput):
            return AssistantResponseEvent(payload=AssistantResponsePayload(text=parsed.text))

        try:
            tool_call = self._validate_tool_call(parsed)
            tool_response = self._execute_tool(tool_call)
        except (ValidationError, ValueError):
            return AssistantResponseEvent(
                payload=AssistantResponsePayload(
                    text="I am missing a detail needed to change that task."
                )
            )
        except TaskNotFoundException:
            return AssistantResponseEvent(
                payload=AssistantResponsePayload(text="I could not find that task.")
            )
        except (DatabaseOperationException, ServiceException):
            return ErrorEvent(
                payload=ErrorPayload(
                    message=SAFE_OPERATION_FAILURE_MESSAGE
                )
            )
        except Exception:
            return ErrorEvent(payload=ErrorPayload(message=SAFE_OPERATION_FAILURE_MESSAGE))

        return tool_response

    def _call_ollama(self, transcript: str) -> str | None:
        payload = {
            "model": OLLAMA_MODEL,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": self._build_user_prompt(transcript),
                },
            ],
            "options": {"temperature": 0.1},
        }

        encoded_payload = json.dumps(payload).encode("utf-8")
        ollama_request = request.Request(
            OLLAMA_URL,
            data=encoded_payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(ollama_request, timeout=OLLAMA_TIMEOUT_SECONDS) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except TimeoutError as exc:
            raise OllamaTimeoutError from exc
        except error.URLError as exc:
            if "timed out" in str(getattr(exc, "reason", exc)).lower():
                raise OllamaTimeoutError from exc
            return None
        except (OSError, json.JSONDecodeError):
            return None

        message = response_payload.get("message", {})
        content = message.get("content")
        return content if isinstance(content, str) else None

    def _build_user_prompt(self, transcript: str) -> str:
        history = "\n".join(
            f"- {recent}" for recent in self.memory.recent_transcript_history[-5:]
        )
        try:
            task_snapshot = "\n".join(
                self._format_task_snapshot(task)
                for task in self.tools.get_all_tasks()
            )
        except Exception:
            task_snapshot = "- unavailable"
        pending = self.memory.pending_confirmation.model_dump() if self.memory.pending_confirmation else None

        return (
            f"Session ID: {self.memory.session_id}\n"
            f"Pending confirmation: {json.dumps(pending)}\n"
            f"Last referenced task ids: {json.dumps(self.memory.last_referenced_task_ids)}\n"
            f"Current task snapshot:\n{task_snapshot or '- no tasks'}\n\n"
            f"Recent transcript history:\n{history or '- none'}\n\n"
            f"Current user transcript:\n{transcript}"
        )

    def _format_task_snapshot(self, task) -> str:
        due_text = task.due_date.isoformat() if task.due_date else "no due date"
        return f"- id={task.id}; title={task.title}; status={task.status}; due_date={due_text}"

    def _parse_llm_output(self, raw_output: str) -> AssistantResponseOutput | ToolCallOutput:
        sanitized_output = self._strip_markdown_json(raw_output)
        payload = json.loads(sanitized_output)

        try:
            return AssistantResponseOutput.model_validate(payload)
        except ValidationError:
            return ToolCallOutput.model_validate(payload)

    def _strip_markdown_json(self, raw_output: str) -> str:
        text = raw_output.strip()
        fence_match = re.fullmatch(
            r"```(?:json)?\s*(.*?)\s*```",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if fence_match:
            return fence_match.group(1).strip()

        return text

    def _validate_tool_call(self, output: ToolCallOutput) -> ToolCall:
        if output.tool == "create_task":
            return ToolCall(
                tool=output.tool,
                arguments=CreateTaskArgs.model_validate(output.arguments),
            )

        if output.tool == "update_task":
            return ToolCall(
                tool=output.tool,
                arguments=UpdateTaskArgs.model_validate(output.arguments),
            )

        if output.tool == "delete_task":
            return ToolCall(
                tool=output.tool,
                arguments=DeleteTaskArgs.model_validate(output.arguments),
            )

        if output.tool == "summarize_agenda":
            return ToolCall(
                tool=output.tool,
                arguments=AgendaArgs.model_validate(output.arguments),
            )

        raise ValueError(f"Unsupported tool: {output.tool}")

    def _handle_local_fallback(
        self,
        transcript: str,
    ) -> AssistantResponseEvent | ActionConfirmationRequiredEvent | ErrorEvent | None:
        normalized = transcript.strip().lower()

        create_match = re.search(
            r"\b(?:create|add|make|remind me to)\b(?:\s+a)?(?:\s+task)?(?:\s+to)?\s+(?P<title>.+)",
            transcript,
            flags=re.IGNORECASE,
        )
        if create_match:
            title = create_match.group("title").strip(" .")
            if title:
                try:
                    return self._execute_tool(
                        ToolCall(
                            tool="create_task",
                            arguments=CreateTaskArgs(title=title),
                        )
                    )
                except Exception:
                    return ErrorEvent(payload=ErrorPayload(message=SAFE_OPERATION_FAILURE_MESSAGE))

        if any(
            phrase in normalized
            for phrase in (
                "what do i have",
                "what are my tasks",
                "show my tasks",
                "agenda",
            )
        ):
            try:
                return self._execute_tool(
                    ToolCall(tool="summarize_agenda", arguments=AgendaArgs())
                )
            except Exception:
                return ErrorEvent(payload=ErrorPayload(message=SAFE_OPERATION_FAILURE_MESSAGE))

        delete_match = re.search(
            r"\b(?:delete|remove)\b(?:\s+the|\s+my|\s+a)?\s+(?P<query>.+?)(?:\s+task)?$",
            transcript,
            flags=re.IGNORECASE,
        )
        if delete_match:
            query = delete_match.group("query").strip(" .")
            if query:
                try:
                    return self._execute_tool(
                        ToolCall(
                            tool="delete_task",
                            arguments=DeleteTaskArgs(query=query, confirmed=False),
                        )
                    )
                except Exception:
                    return ErrorEvent(payload=ErrorPayload(message=SAFE_OPERATION_FAILURE_MESSAGE))

        return None

    def _execute_tool(
        self,
        tool_call: ToolCall,
    ) -> AssistantResponseEvent | ActionConfirmationRequiredEvent:
        try:
            if tool_call.tool == "create_task" and isinstance(tool_call.arguments, CreateTaskArgs):
                tool_result = self.tools.create_task(tool_call.arguments)
                self.memory.remember_task_ids(tool_result.task_ids)
                return AssistantResponseEvent(
                    payload=AssistantResponsePayload(text=tool_result.spoken_text)
                )

            if tool_call.tool == "update_task" and isinstance(tool_call.arguments, UpdateTaskArgs):
                tool_result = self.tools.update_task(tool_call.arguments)
                self.memory.remember_task_ids(tool_result.task_ids)
                return AssistantResponseEvent(
                    payload=AssistantResponsePayload(text=tool_result.spoken_text)
                )

            if tool_call.tool == "delete_task" and isinstance(tool_call.arguments, DeleteTaskArgs):
                return self._handle_delete_request(tool_call.arguments)

            if tool_call.tool == "summarize_agenda" and isinstance(tool_call.arguments, AgendaArgs):
                tasks = self.tools.get_tasks_for_date(tool_call.arguments.date)
                self.memory.remember_task_ids([str(task.id) for task in tasks])
                tool_result = self.tools.summarize_agenda(tool_call.arguments)
                return AssistantResponseEvent(
                    payload=AssistantResponsePayload(text=tool_result.spoken_text)
                )
        except (TaskNotFoundException, DatabaseOperationException, ServiceException):
            raise
        except Exception as exc:
            raise ServiceException(SAFE_OPERATION_FAILURE_MESSAGE) from exc

        raise ValueError("Tool arguments did not match tool name")

    def _handle_delete_request(
        self,
        args: DeleteTaskArgs,
    ) -> AssistantResponseEvent | ActionConfirmationRequiredEvent:
        if args.task_id:
            return self._prepare_delete_confirmation(
                query=str(args.task_id),
                candidate_task_ids=[str(args.task_id)],
            )

        if not args.query:
            return AssistantResponseEvent(
                payload=AssistantResponsePayload(
                    text="Which task would you like me to delete?"
                )
            )

        try:
            matches = self.tools.find_tasks_by_query(args.query)
        except Exception as exc:
            raise ServiceException(SAFE_OPERATION_FAILURE_MESSAGE) from exc
        candidate_task_ids = [str(task.id) for task in matches]
        self.memory.remember_task_ids(candidate_task_ids)

        if not matches:
            return AssistantResponseEvent(
                payload=AssistantResponsePayload(
                    text=f"I could not find a task matching {args.query}."
                )
            )

        return self._prepare_delete_confirmation(args.query, candidate_task_ids)

    def _prepare_delete_confirmation(
        self,
        query: str,
        candidate_task_ids: list[str],
    ) -> ActionConfirmationRequiredEvent:
        self.memory.set_pending_delete(query=query, candidate_task_ids=candidate_task_ids)

        if len(candidate_task_ids) == 1:
            task_title = self._find_task_title(candidate_task_ids[0])
            return ActionConfirmationRequiredEvent(
                payload=ActionConfirmationRequiredPayload(
                    text=f"Please confirm: should I delete {task_title}?"
                )
            )

        choices = self._format_delete_choices(candidate_task_ids)
        return ActionConfirmationRequiredEvent(
            payload=ActionConfirmationRequiredPayload(
                text=f"I found multiple matching tasks: {choices}. Which one should I delete?"
            )
        )

    def _try_handle_pending_confirmation(
        self,
        transcript: str,
    ) -> AssistantResponseEvent | ActionConfirmationRequiredEvent | ErrorEvent | None:
        pending = self.memory.pending_confirmation
        if pending is None:
            return None

        normalized = transcript.lower().strip()

        if normalized in {"cancel", "never mind", "nevermind", "stop", "no"}:
            self.memory.clear_pending_confirmation()
            return AssistantResponseEvent(
                payload=AssistantResponsePayload(text="Okay, I will leave it as is.")
            )

        selected_task_id = self._resolve_pending_delete_selection(transcript)

        if selected_task_id is None:
            choices = self._format_delete_choices(pending.candidate_task_ids)
            return ActionConfirmationRequiredEvent(
                payload=ActionConfirmationRequiredPayload(
                    text=f"Which one should I delete: {choices}?"
                )
            )

        try:
            tool_result = self.tools.delete_task(
                DeleteTaskArgs(task_id=uuid.UUID(selected_task_id), confirmed=True)
            )
        except TaskNotFoundException:
            self.memory.clear_pending_confirmation()
            return AssistantResponseEvent(
                payload=AssistantResponsePayload(text="I could not find that task.")
            )
        except (DatabaseOperationException, ServiceException):
            return ErrorEvent(
                payload=ErrorPayload(
                    message=SAFE_OPERATION_FAILURE_MESSAGE
                )
            )
        except Exception:
            return ErrorEvent(payload=ErrorPayload(message=SAFE_OPERATION_FAILURE_MESSAGE))

        self.memory.remember_task_ids([selected_task_id])
        self.memory.clear_pending_confirmation()
        return AssistantResponseEvent(payload=AssistantResponsePayload(text=tool_result.spoken_text))

    def _resolve_pending_delete_selection(self, transcript: str) -> str | None:
        pending = self.memory.pending_confirmation
        if pending is None:
            return None

        normalized = transcript.lower().strip()
        candidate_task_ids = pending.candidate_task_ids

        if len(candidate_task_ids) == 1 and normalized in {
            "yes",
            "confirm",
            "confirmed",
            "delete it",
            "delete that",
            "go ahead",
            "please do",
        }:
            return candidate_task_ids[0]

        ordinal_map = {
            "first": 0,
            "one": 0,
            "1": 0,
            "second": 1,
            "two": 1,
            "2": 1,
            "third": 2,
            "three": 2,
            "3": 2,
            "fourth": 3,
            "four": 3,
            "4": 3,
            "fifth": 4,
            "five": 4,
            "5": 4,
        }

        normalized_tokens = set(re.findall(r"\b\w+\b", normalized))

        for phrase, index in ordinal_map.items():
            if phrase in normalized_tokens and index < len(candidate_task_ids):
                return candidate_task_ids[index]

        for task_id in candidate_task_ids:
            title = self._find_task_title(task_id).lower()
            if title and title in normalized:
                return task_id

        return None

    def _format_delete_choices(self, task_ids: list[str]) -> str:
        titles = [self._find_task_title(task_id) for task_id in task_ids]

        if len(titles) <= 2:
            return " or ".join(titles)

        return f"{', '.join(titles[:-1])}, or {titles[-1]}"

    def _find_task_title(self, task_id: str) -> str:
        try:
            for task in self.tools.get_all_tasks():
                if str(task.id) == task_id:
                    return task.title
        except Exception:
            return "that task"

        return "that task"
