from app.repository.base_repository import BaseRepository
from app.model.task_time_log import TaskTimeLog
from sqlalchemy import func
from app.model.user import User
from app.model.task import Task
from app.model.task_type import TaskType


class TaskTimeLogRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(session_factory, TaskTimeLog)

    def get_velocity_profile_by_user(self, project_id: str):
        with self.session_factory() as session:
            rows = (
                session.query(
                    User.id,
                    User.name,
                    User.email,
                    func.sum(TaskTimeLog.hours).label("total_hours"),
                    func.count(TaskTimeLog.id).label("log_count"),
                )
                .join(TaskTimeLog, TaskTimeLog.user_id == User.id)
                .join(Task, Task.id == TaskTimeLog.task_id)
                .filter(Task.project_id == project_id)
                .group_by(User.id, User.name, User.email)
                .all()
            )
            return rows

    def get_velocity_profile_by_task_type(self, project_id: str):
        with self.session_factory() as session:
            rows = (
                session.query(
                    TaskType.id,
                    TaskType.name,
                    TaskType.color,
                    func.sum(TaskTimeLog.hours).label("total_hours"),
                    func.count(TaskTimeLog.id).label("log_count"),
                )
                .join(Task, Task.type_id == TaskType.id)
                .join(TaskTimeLog, TaskTimeLog.task_id == Task.id)
                .filter(Task.project_id == project_id)
                .group_by(TaskType.id, TaskType.name, TaskType.color)
                .all()
            )
            return rows

    def get_logs_for_project(self, project_id: str):
        with self.session_factory() as session:
            logs = (
                session.query(TaskTimeLog.logged_date, TaskTimeLog.hours)
                .join(Task, Task.id == TaskTimeLog.task_id)
                .filter(Task.project_id == project_id)
                .all()
            )
            return logs
