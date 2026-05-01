from typing import Any
from app.services.base_service import BaseService


class TaskService(BaseService):
    def __init__(self, repository: Any) -> None:
        super().__init__(repository)

    def add(self, schema: Any) -> Any:
        return super().add(schema)

    def patch(self, id: str, schema: Any) -> Any:
        return super().patch(id, schema)

    def patch_attr(self, id: str, attr: str, value: Any) -> Any:
        return super().patch_attr(id, attr, value)

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
