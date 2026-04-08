from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.model.base_model import BaseModel


class Database:
    def __init__(self, db_url: str) -> None:
        self._engine = create_engine(db_url, echo=False)
        self._session_factory = sessionmaker(autocommit=False, autoflush=False, bind=self._engine, expire_on_commit=False)

    def create_database(self) -> None:
        BaseModel.metadata.create_all(self._engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        session: Session = self._session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
