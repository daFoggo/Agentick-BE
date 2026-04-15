from app.repository.base_repository import BaseRepository
from app.model.task_type import TaskType


class TaskTypeRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(session_factory, TaskType)
