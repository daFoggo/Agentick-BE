from app.repository.base_repository import BaseRepository
from app.model.phase import Phase


class PhaseRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(session_factory, Phase)
