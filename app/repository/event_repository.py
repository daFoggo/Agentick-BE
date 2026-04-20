from contextlib import AbstractContextManager
from typing import Callable
from sqlalchemy.orm import Session

from app.model.event import Event
from app.repository.base_repository import BaseRepository


class EventRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]) -> None:
        super().__init__(session_factory, Event)
