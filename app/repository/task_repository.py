from app.repository.base_repository import BaseRepository
from app.model.task import Task


class TaskRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(session_factory, Task)
