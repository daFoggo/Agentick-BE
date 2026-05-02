from contextlib import AbstractContextManager
from typing import Callable
from sqlalchemy.orm import Session

from app.model.calendar import Calendar
from app.repository.base_repository import BaseRepository


class CalendarRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]) -> None:
        super().__init__(session_factory, Calendar)
