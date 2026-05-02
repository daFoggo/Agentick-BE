from datetime import datetime
from typing import Optional, Any

from app.model.task import Task
from app.model.project_member import ProjectMember
from app.repository.project_member_repository import ProjectMemberRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.repository.event_repository import EventRepository
from app.schema.event_schema import EventCreate, EventUpdate
from app.services.calendar_service import CalendarService
from app.services.base_service import BaseService


class TaskCalendarSyncService(BaseService):
    def __init__(
        self,
        event_repository: EventRepository,
        project_member_repository: ProjectMemberRepository,
        team_member_repository: TeamMemberRepository,
        calendar_service: CalendarService,
        task_repository: Any = None, # Avoid circular import if needed
    ) -> None:
        super().__init__(event_repository)
        self._event_repo = event_repository
        self._project_member_repo = project_member_repository
        self._team_member_repo = team_member_repository
        self._calendar_service = calendar_service
        self._task_repo = task_repository

    def sync_task_event(self, task_or_id: Any):
        """
        Syncs a task to a 'task' event on each assignee's personal calendar.
        """
        task_id = task_or_id.id if hasattr(task_or_id, "id") else task_or_id
        
        # 1. Fetch task with all needed relations to ensure they are loaded
        if self._task_repo:
            task = self._task_repo.read_by_id(task_id, eager=True)
        else:
            task = task_or_id

        # 2. Clear existing events for this task
        self._calendar_service.delete_task_event(task.id)

        # 3. If no assignees, no dates, or task is inactive, we are done
        if (
            not task.assignees 
            or (not task.start_date and not task.due_date)
            or getattr(task, "is_deleted", False)
            or getattr(task, "is_archived", False)
        ):
            return

        # 4. Resolve team_id from project
        team_id = getattr(task.project, "team_id", None)
        if not team_id:
            return

        # 5. Determine event times
        start_time = task.start_date or task.due_date
        end_time = task.due_date or task.start_date
        
        if not start_time or not end_time:
            return

        # 6. Create event for each assignee
        for member in task.assignees:
            user_id = getattr(member, "user_id", None)
            if not user_id:
                continue
            
            # Ensure user name is available
            user_name = "User"
            if member.user:
                user_name = member.user.name
            else:
                # Eager load user if missing
                member = self._project_member_repo.read_by_id(member.id, eager=True)
                if member and member.user:
                    user_name = member.user.name

            # Get/Create personal calendar
            self._calendar_service.get_or_create_personal_calendar(user_id, user_name)

            # Find TeamMember record to get the correct participant_id
            team_member = self._team_member_repo.read_by_options({
                "team_id__eq": team_id,
                "user_id__eq": user_id
            })
            
            participant_ids = []
            if team_member and team_member["founds"]:
                participant_ids = [team_member["founds"][0].id]

            # Create new event
            event_schema = EventCreate(
                user_id=user_id,
                team_id=team_id,
                type="task",
                title=task.title,
                description=task.description,
                start_time=start_time,
                end_time=end_time,
                task_id=task.id,
                participant_ids=participant_ids
            )
            self._event_repo.create(event_schema)
