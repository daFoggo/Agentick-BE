from app.repository.base_repository import BaseRepository
from app.model.task_status import TaskStatus


class TaskStatusRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(session_factory, TaskStatus)
