"""
Deterministic task tools used by the voice orchestrator.
"""

import uuid
from datetime import date as Date

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from backend.enums.task_statuses import TaskStatus
from backend.schema.task_schema import TaskCreate, TaskResponse, TaskUpdate
from backend.services.task_service import TaskServices


class CreateTaskArgs(BaseModel):
    title: str
    status: TaskStatus = TaskStatus.TODO
    due_date: str | None = Field(
        default=None,
        validation_alias=AliasChoices("dueDate", "due_date"),
    )
    model_config = ConfigDict(populate_by_name=True)


class UpdateTaskArgs(BaseModel):
    task_id: uuid.UUID = Field(validation_alias=AliasChoices("taskId", "task_id"))
    title: str | None = None
    status: TaskStatus | None = None
    due_date: str | None = Field(
        default=None,
        validation_alias=AliasChoices("dueDate", "due_date"),
    )
    model_config = ConfigDict(populate_by_name=True)


class DeleteTaskArgs(BaseModel):
    task_id: uuid.UUID | None = Field(
        default=None,
        validation_alias=AliasChoices("taskId", "task_id"),
    )
    query: str | None = None
    confirmed: bool = False
    model_config = ConfigDict(populate_by_name=True)


class AgendaArgs(BaseModel):
    date: Date | None = None


class ToolResult(BaseModel):
    spoken_text: str
    task_ids: list[str] = Field(default_factory=list)


def _format_task(task: TaskResponse) -> str:
    due_text = f" for {task.due_date.isoformat()}" if task.due_date else ""
    return f"{task.title}{due_text}"


class VoiceTaskTools:
    def __init__(self, task_services: TaskServices, user_id: uuid.UUID) -> None:
        self.task_services = task_services
        self.user_id = user_id

    def create_task(self, args: CreateTaskArgs) -> ToolResult:
        task = self.task_services.create(
            TaskCreate.model_validate(args.model_dump(exclude_none=True)),
            self.user_id,
        )
        return ToolResult(
            spoken_text=f"I added {_format_task(task)}.",
            task_ids=[str(task.id)],
        )

    def update_task(self, args: UpdateTaskArgs) -> ToolResult:
        task_data = args.model_dump(exclude={"task_id"}, exclude_none=True)
        task = self.task_services.update(
            args.task_id,
            self.user_id,
            TaskUpdate.model_validate(task_data),
        )
        return ToolResult(
            spoken_text=f"I updated {_format_task(task)}.",
            task_ids=[str(task.id)],
        )

    def delete_task(self, args: DeleteTaskArgs) -> ToolResult:
        if not args.task_id:
            return ToolResult(spoken_text="I need to know which task to delete.")

        if not args.confirmed:
            return ToolResult(
                spoken_text="Please confirm which task to delete before I remove it."
            )

        self.task_services.delete(args.task_id, self.user_id)
        return ToolResult(spoken_text="I deleted that task.", task_ids=[str(args.task_id)])

    def get_all_tasks(self) -> list[TaskResponse]:
        return self.task_services.get_all(self.user_id)

    def find_tasks_by_query(self, query: str) -> list[TaskResponse]:
        normalized_query = _normalize(query)
        if not normalized_query:
            return []

        query_tokens = set(normalized_query.split())
        matches: list[TaskResponse] = []

        for task in self.get_all_tasks():
            normalized_title = _normalize(task.title)
            title_tokens = set(normalized_title.split())

            if normalized_query in normalized_title or query_tokens.intersection(title_tokens):
                matches.append(task)

        return matches

    def get_tasks_for_date(self, target_date: Date | None) -> list[TaskResponse]:
        tasks = self.get_all_tasks()

        if target_date is None:
            return tasks

        return [task for task in tasks if task.due_date and task.due_date.date() == target_date]

    def summarize_agenda(self, args: AgendaArgs) -> ToolResult:
        tasks = self.get_tasks_for_date(args.date)

        if not tasks:
            day_text = "that day" if args.date else "right now"
            return ToolResult(spoken_text=f"You do not have any tasks for {day_text}.")

        task_titles = [task.title for task in tasks]
        day_text = args.date.isoformat() if args.date else "your agenda"

        if len(task_titles) == 1:
            return ToolResult(spoken_text=f"For {day_text}, you have {task_titles[0]}.")

        if len(task_titles) == 2:
            joined_titles = " and ".join(task_titles)
        else:
            joined_titles = f"{', '.join(task_titles[:-1])}, and {task_titles[-1]}"

        return ToolResult(
            spoken_text=f"For {day_text}, you have {len(task_titles)} tasks: {joined_titles}."
        )


def _normalize(value: str) -> str:
    return " ".join(
        token
        for token in "".join(character.lower() if character.isalnum() else " " for character in value).split()
        if token not in {"the", "a", "an", "task", "todo", "to", "my"}
    )
