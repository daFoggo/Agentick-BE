from contextlib import contextmanager

import pytest

from app.repository.unit_of_work import UnitOfWork


class FakeSession:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class FakeRepository:
    instances = 0

    def __init__(self, session_factory):
        FakeRepository.instances += 1
        self.session_factory = session_factory

    def get_session(self):
        with self.session_factory() as session:
            return session


@contextmanager
def fake_session_factory():
    session = FakeSession()
    yield session


def test_unit_of_work_lazily_reuses_repository_instance():
    FakeRepository.instances = 0

    with UnitOfWork(fake_session_factory) as uow:
        repository = uow.get_repo(FakeRepository)
        same_repository = uow.get_repo(FakeRepository)

        assert repository is same_repository
        assert repository.get_session() is uow.session

    assert FakeRepository.instances == 1
    assert uow.session.committed is True
    assert uow.session.rolled_back is False


def test_unit_of_work_rolls_back_on_error():
    with pytest.raises(ValueError):
        with UnitOfWork(fake_session_factory) as uow:
            session = uow.session
            raise ValueError("fail")

    assert session.committed is False
    assert session.rolled_back is True
