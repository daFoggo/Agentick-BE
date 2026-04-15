from app.repository.base_repository import BaseRepository
from app.model.tag import Tag


class TagRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(session_factory, Tag)
