from app.core.config import settings
from app.core.database import Database


class Container:
    def __init__(self) -> None:
        self._db: Database | None = None

    @property
    def db(self) -> Database:
        if self._db is None:
            self._db = Database(settings.DATABASE_URI)
        return self._db
