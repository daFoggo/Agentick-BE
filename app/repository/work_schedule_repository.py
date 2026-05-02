from contextlib import AbstractContextManager
from typing import Callable
from sqlalchemy.orm import Session

from app.model.work_schedule import WorkSchedule
from app.repository.base_repository import BaseRepository


class WorkScheduleRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]) -> None:
        super().__init__(session_factory, WorkSchedule)
