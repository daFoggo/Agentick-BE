from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.team import Team
from app.repository.base_repository import BaseRepository


class TeamRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]) -> None:
        super().__init__(session_factory=session_factory, model=Team)
