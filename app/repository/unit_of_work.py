from contextlib import nullcontext
from app.repository.project_repository import ProjectRepository
from app.repository.project_member_repository import ProjectMemberRepository
from app.repository.task_status_repository import TaskStatusRepository
from app.repository.task_type_repository import TaskTypeRepository
from app.repository.task_priority_repository import TaskPriorityRepository


class UnitOfWork:
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._cm = None
        self.session = None

    def __enter__(self):
        # Correctly invoke the context manager to resolve the actual Session
        self._cm = self.session_factory()
        self.session = self._cm.__enter__()

        # Create wrapper factory that injects our active session
        # instead of creating a new one
        def active_session_factory():
            return nullcontext(self.session)

        # Inject repositories configured with current atomic session
        self.projects = ProjectRepository(active_session_factory)
        self.project_members = ProjectMemberRepository(active_session_factory)
        self.task_statuses = TaskStatusRepository(active_session_factory)
        self.task_types = TaskTypeRepository(active_session_factory)
        self.task_priorities = TaskPriorityRepository(active_session_factory)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                self.session.rollback()
            else:
                self.session.commit()
        finally:
            # This triggers the final step of the session (e.g. close, or do nothing for nullcontext)
            self._cm.__exit__(exc_type, exc_val, exc_tb)
