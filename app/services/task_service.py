from typing import Any
from app.services.base_service import BaseService


class TaskService(BaseService):
    def __init__(self, repository: Any) -> None:
        super().__init__(repository)

    def add(self, schema: Any) -> Any:
        item = super().add(schema)
        return self.get_by_id(item.id)

    def get_list(self, schema: Any) -> Any:
        """Lấy danh sách task kèm eager load relationships (mặc định cho Task)."""
        return self._repository.read_by_options(schema, eager=True)

    def get_list_eager(self, schema: Any) -> Any:
        return self.get_list(schema)

    def get_by_id(self, id: str) -> Any:
        return self._repository.read_by_id(id, eager=True)

    def patch(self, id: str, schema: Any, user_id: str = None) -> Any:
        return self._repository.update(id, schema, eager=True, user_id=user_id)

    def patch_attr(self, id: str, attr: str, value: Any, user_id: str = None) -> Any:
        # Since update_attr doesn't use the full update logic, if we need activity on single attr we might need to route it to update
        # But for now, we just pass eager=True
        return self._repository.update_attr(id, attr, value, eager=True)

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
