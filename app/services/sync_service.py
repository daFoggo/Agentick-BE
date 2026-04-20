from datetime import datetime
from typing import Optional

from app.model.task import Task
from app.model.project_member import ProjectMember
from app.repository.project_member_repository import ProjectMemberRepository
from app.repository.event_repository import EventRepository
from app.schema.event_schema import EventCreate, EventUpdate
from app.services.calendar_service import CalendarService
from app.services.base_service import BaseService


class TaskCalendarSyncService(BaseService):
    def __init__(
        self,
        event_repository: EventRepository,
        project_member_repository: ProjectMemberRepository,
        calendar_service: CalendarService,
    ) -> None:
        super().__init__(event_repository)
        self._event_repo = event_repository
        self._project_member_repo = project_member_repository
        self._calendar_service = calendar_service

    def sync_task_block(self, task: Task):
        """
        Syncs a task to a 'task_block' event on the assignee's personal calendar.
        """
        # 1. Clear existing event for this task
        self._calendar_service.delete_task_block_event(task.id)

        # 2. If no assignee, no dates, or task is inactive, we are done
        if (
            not task.assignee_id 
            or (not task.start_date and not task.due_date)
            or task.is_deleted 
            or task.is_archived
        ):
            return

        # 3. Resolve user_id from project_member_id
        member = self._project_member_repo.read_by_id(task.assignee_id, eager=True)
        if not member or not member.user:
            return
        
        user_id = member.user_id
        user_name = member.user.name

        # 4. Get/Create personal calendar
        calendar = self._calendar_service.get_or_create_personal_calendar(user_id, user_name)

        # 5. Resolve team_id from project
        team_id = task.project.team_id

        # 6. Determine event times
        start_time = task.start_date or task.due_date
        end_time = task.due_date or task.start_date
        
        # 7. Create new event
        event_schema = EventCreate(
            calendar_id=calendar.id,
            user_id=user_id,
            team_id=team_id,
            type="task_block",
            title=task.title,
            description=task.description,
            start_time=start_time,
            end_time=end_time,
            task_id=task.id
        )
        self._event_repo.create(event_schema)
