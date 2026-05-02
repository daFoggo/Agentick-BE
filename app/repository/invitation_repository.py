from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Sequence

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.model.invitation import Invitation, InvitationStatus
from app.repository.base_repository import BaseRepository

class InvitationRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]):
        super().__init__(session_factory, Invitation)

    def get_pending_by_email(self, email: str, eager: bool = False) -> Sequence[Invitation]:
        with self.session_factory() as session:
            query = select(self.model).filter(
                self.model.email == email,
                self.model.status == InvitationStatus.PENDING
            )
            if eager:
                from sqlalchemy.orm import joinedload
                for relation in getattr(self.model, "eagers", []):
                    query = query.options(joinedload(getattr(self.model, relation)))
            
            return session.execute(query).scalars().all()
