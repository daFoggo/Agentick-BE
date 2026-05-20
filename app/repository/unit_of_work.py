from contextlib import nullcontext
from typing import TypeVar, cast

from app.repository.base_repository import BaseRepository

RepositoryT = TypeVar("RepositoryT", bound=BaseRepository)


class UnitOfWork:
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._cm = None
        self.session = None
        self._repositories: dict[type[BaseRepository], BaseRepository] = {}

    def __enter__(self):
        # Correctly invoke the context manager to resolve the actual Session
        self._cm = self.session_factory()
        self.session = self._cm.__enter__()
        self._repositories = {}
        return self

    def get_repo(self, repository_class: type[RepositoryT]) -> RepositoryT:
        if self.session is None:
            raise RuntimeError(
                "UnitOfWork must be entered before requesting repositories."
            )
        if repository_class not in self._repositories:
            self._repositories[repository_class] = repository_class(
                lambda: nullcontext(self.session)
            )
        return cast(RepositoryT, self._repositories[repository_class])

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                self.session.rollback()
            else:
                self.session.commit()
        finally:
            # This triggers the final step of the session (e.g. close, or do nothing for nullcontext)
            self._cm.__exit__(exc_type, exc_val, exc_tb)
