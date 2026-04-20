from typing import Any
from app.services.base_service import BaseService
from app.services.sync_service import TaskCalendarSyncService


class TaskService(BaseService):
    def __init__(self, repository: Any, sync_service: TaskCalendarSyncService) -> None:
        super().__init__(repository)
        self._sync_service = sync_service

    def add(self, schema: Any) -> Any:
        task = super().add(schema)
        # Sync to calendar
        self._sync_service.sync_task_block(task)
        return task

    def patch(self, id: str, schema: Any) -> Any:
        task = super().patch(id, schema)
        # Sync to calendar
        self._sync_service.sync_task_block(task)
        return task

    def patch_attr(self, id: str, attr: str, value: Any) -> Any:
        task = super().patch_attr(id, attr, value)
        self._sync_service.sync_task_block(task)
        return task

    def get_gantt_data(self, project_id: str):
        """
        Fetches all tasks for a project, including phase and assignee info.
        """
        # Using read_by_options with eager=True to get status, phase, assignee
        result = self._repository.read_by_options(
            {"project_id__eq": project_id, "is_deleted__eq": False, "page_size": "all"},
            eager=True
        )
        return result["founds"]
