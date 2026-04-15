from app.repository.base_repository import BaseRepository
from app.model.task_priority import TaskPriority


class TaskPriorityRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(session_factory, TaskPriority)
