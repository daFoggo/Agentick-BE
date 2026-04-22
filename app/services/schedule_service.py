from datetime import date
from typing import Optional, Any, List

from app.repository.work_schedule_repository import WorkScheduleRepository
from app.schema.schedule_schema import WorkScheduleRead, WorkScheduleCreate
from app.services.base_service import BaseService


class ScheduleService(BaseService):
    def __init__(
        self,
        work_schedule_repository: WorkScheduleRepository,
    ) -> None:
        super().__init__(work_schedule_repository)
        self._work_schedule_repo = work_schedule_repository

    def get_user_patterns(self, user_id: str):
        """
        Returns the 7-day weekly pattern for a user.
        """
        return self._work_schedule_repo.read_by_options(
            {"user_id__eq": user_id}
        )["founds"]

    def upsert_pattern(self, schema: WorkScheduleCreate):
        """
        Creates or updates a single day pattern for a user.
        """
        existing = self._work_schedule_repo.read_by_options({
            "user_id__eq": schema.user_id,
            "day_of_week__eq": schema.day_of_week
        })["founds"]
        
        if existing:
            return self._work_schedule_repo.update(existing[0].id, schema.model_dump(exclude_unset=True))
        else:
            return self._work_schedule_repo.create(schema)

    def create_default_user_schedule(self, user_id: str):
        """
        Create default schedule for a user (Mon-Fri 08:00-17:00, Sat-Sun Off)
        """
        from app.schema.schedule_schema import WorkScheduleCreate
        
        # Mon-Fri
        for day in range(5):
            self._work_schedule_repo.create(WorkScheduleCreate(
                user_id=user_id,
                day_of_week=day,
                start_time="08:00",
                end_time="17:00",
                is_off=False
            ), auto_commit=False)
            
        # Sat-Sun
        for day in range(5, 7):
            self._work_schedule_repo.create(WorkScheduleCreate(
                user_id=user_id,
                day_of_week=day,
                is_off=True
            ), auto_commit=False)
