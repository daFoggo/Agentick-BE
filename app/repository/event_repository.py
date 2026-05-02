from contextlib import AbstractContextManager
from typing import Callable
from sqlalchemy.orm import Session

from app.model.event import Event
from app.model.team_member import TeamMember
from app.repository.base_repository import BaseRepository
from app.core.exceptions import NotFoundError


class EventRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]) -> None:
        super().__init__(session_factory, Event)

    def create(self, schema, auto_commit=True):
        data = schema.model_dump() if hasattr(schema, "model_dump") else schema
        participant_ids = data.pop("participant_ids", [])
        with self.session_factory() as session:
            item = self.model(**data)
            if participant_ids:
                participants = session.query(TeamMember).filter(TeamMember.id.in_(participant_ids)).all()
                item.participants = participants
            session.add(item)
            if auto_commit:
                session.commit()
                session.refresh(item)
            else:
                session.flush()
            return item

    def update(self, id, schema, auto_commit=True):
        data = schema.model_dump(exclude_none=True) if hasattr(schema, "model_dump") else schema
        participant_ids = data.pop("participant_ids", None)
        with self.session_factory() as session:
            item = session.query(self.model).filter(self.model.id == id).first()
            if not item:
                raise NotFoundError(detail=f"not found id : {id}")
            
            for key, value in data.items():
                setattr(item, key, value)
            
            if participant_ids is not None:
                participants = session.query(TeamMember).filter(TeamMember.id.in_(participant_ids)).all()
                item.participants = participants
            
            if auto_commit:
                session.commit()
                session.refresh(item)
            return item
