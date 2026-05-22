from typing import Any
from app.services.base_service import BaseService


class TaskService(BaseService):
    def __init__(self, repository: Any, project_member_repo: Any = None) -> None:
        super().__init__(repository)
        self.project_member_repo = project_member_repo

    def add(self, schema: Any, acting_user_id: str = None) -> Any:
        result = self._repository.create(schema, acting_user_id=acting_user_id)
        
        member_ids = set()
        if hasattr(schema, "member_ids") and schema.member_ids:
            member_ids.update(schema.member_ids)
        if acting_user_id:
            member_ids.add(acting_user_id)
            
        if member_ids:
            self._repository.create_task_assignment_notifications(
                result.id, list(member_ids)
            )
            
        return self.get_by_id(result.id)

    def get_list(self, schema: Any) -> Any:
        """Lấy danh sách task kèm eager load relationships (mặc định cho Task)."""
        return self._repository.read_by_options(schema, eager=True)

    def get_list_eager(self, schema: Any) -> Any:
        return self.get_list(schema)

    def get_by_id(self, id: str) -> Any:
        return self._repository.read_by_id(id, eager=True)

    def patch(self, id: str, schema: Any, user_id: str = None) -> Any:
        old_member_ids = set()
        if hasattr(schema, "member_ids") and schema.member_ids is not None:
            old_member_ids = self._repository.get_task_member_ids(id)

        result = self._repository.update(id, schema, eager=True, user_id=user_id)

        if hasattr(schema, "member_ids") and schema.member_ids is not None:
            new_member_ids = set(schema.member_ids)
            added_ids = new_member_ids - old_member_ids
            if added_ids:
                self._repository.create_task_assignment_notifications(
                    result.id, list(added_ids)
                )
        return result

    def patch_attr(self, id: str, attr: str, value: Any, user_id: str = None) -> Any:
        # Since update_attr doesn't use the full update logic, if we need activity on single attr we might need to route it to update
        # But for now, we just pass eager=True
        return self._repository.update_attr(id, attr, value, eager=True)

    def get_gantt_data(self, project_id: str):
        """
        Fetches all tasks for a project, including assignee info.
        """
        # Using read_by_options with eager=True to get status, assignee
        result = self._repository.read_by_options(
            {"project_id__eq": project_id, "is_deleted__eq": False, "page_size": "all"},
            eager=True,
        )
        return result["founds"]

    def get_my_tasks(self, user_id: str, team_id: str | None = None):
        if not self.project_member_repo:
            return []
        user_member_ids = self.project_member_repo.get_member_ids_by_user(user_id)
        if not user_member_ids:
            return []
        return self._repository.get_my_tasks_complex(
            user_id=user_id, user_member_ids=user_member_ids, team_id=team_id
        )

    def get_my_tasks_overview(
        self, user_id: str, team_id: str | None = None, client_today=None
    ):
        if not self.project_member_repo:
            return {"in_progress": [], "upcoming": [], "overdue": []}
        user_member_ids = self.project_member_repo.get_member_ids_by_user(user_id)
        if not user_member_ids:
            return {"in_progress": [], "upcoming": [], "overdue": []}
        return self._repository.get_my_tasks_overview(
            user_id=user_id,
            user_member_ids=user_member_ids,
            team_id=team_id,
            client_today=client_today,
        )

    def get_project_stats(self, project_id: str, period: str):
        from datetime import datetime, timedelta, timezone
        from app.schema.task_schema import ProjectTaskStats, TaskStatItem

        now = datetime.now(timezone.utc)
        delta = timedelta(days=7) if period == "weekly" else timedelta(days=30)
        date_from = now - delta
        date_to = now

        priority_rows, status_rows, type_rows = (
            self._repository.get_project_task_stats_raw(project_id, date_from, date_to)
        )

        by_priority = [
            TaskStatItem(id=r[0], name=r[1], color=r[2], count=r[3])
            for r in priority_rows
        ]
        by_status = [
            TaskStatItem(id=r[0], name=r[1], color=r[2], count=r[3])
            for r in status_rows
        ]
        by_type = [
            TaskStatItem(id=r[0], name=r[1], color=r[2], count=r[3]) for r in type_rows
        ]

        return ProjectTaskStats(
            by_priority=by_priority,
            by_status=by_status,
            by_type=by_type,
            period=period,
            date_from=date_from.date().isoformat(),
            date_to=date_to.date().isoformat(),
        )

    def get_risk_stats(self, project_id: str):
        from datetime import datetime, timezone

        active_tasks, snapshots = self._repository.get_project_risk_data(project_id)

        if not active_tasks:
            return {"overall_risk_index": 0, "tasks": []}

        task_map = {t.id: t for t in active_tasks}
        latest_snapshots = {}
        for s in snapshots:
            if s.task_id not in latest_snapshots:
                latest_snapshots[s.task_id] = s

        result_tasks = []
        total_score = 0.0
        count = 0
        now = datetime.now(timezone.utc)

        for task_id, snap in latest_snapshots.items():
            task = task_map[task_id]
            days_remaining = 0
            if task.due_date:
                delta = task.due_date - now
                days_remaining = delta.days

            total_score += snap.risk_score
            count += 1

            assignee_name = "Unassigned"
            try:
                if (
                    task.task_members
                    and len(task.task_members) > 0
                    and task.task_members[0].user
                ):
                    assignee_name = task.task_members[0].user.name
            except Exception:
                pass

            result_tasks.append(
                {
                    "task_id": task.id,
                    "title": task.title,
                    "assignee_name": assignee_name,
                    "estimated_hours": task.estimated_hours or 0,
                    "actual_hours": task.actual_hours or 0,
                    "days_remaining": days_remaining,
                    "risk_score": snap.risk_score,
                    "risk_level": snap.risk_level,
                    "recommendation": snap.recommendation,
                    "signals": snap.signals,
                    "created_at": snap.created_at.isoformat()
                    if snap.created_at
                    else None,
                }
            )

        overall_risk = (total_score / count) if count > 0 else 0.0
        return {"overall_risk_index": overall_risk, "tasks": result_tasks}

    def get_recent_updates(self, project_id: str, limit: int):
        activities, status_map = self._repository.get_recent_updates_raw(
            project_id, limit
        )
        results = []

        for activity in activities:
            old_status = (
                status_map.get(activity.old_value, {}) if activity.old_value else {}
            )
            new_status = (
                status_map.get(activity.new_value, {}) if activity.new_value else {}
            )

            results.append(
                {
                    "id": activity.id,
                    "task_id": activity.task_id,
                    "task_title": activity.task.title
                    if activity.task
                    else "Unknown Task",
                    "user_id": activity.user_id,
                    "user_name": activity.user.name if activity.user else "System",
                    "field_changed": activity.field_name,
                    "old_value": activity.old_value,
                    "new_value": activity.new_value,
                    "old_status_name": old_status.get("name") or activity.old_value,
                    "old_status_color": old_status.get("color"),
                    "new_status_name": new_status.get("name") or activity.new_value,
                    "new_status_color": new_status.get("color"),
                    "created_at": activity.created_at.isoformat()
                    if activity.created_at
                    else None,
                }
            )
        return results

    def start_task(self, id: str, user_id: str) -> Any:
        from datetime import datetime, timezone
        from app.model.task_checkpoint import TaskCheckpoint
        from app.model.task_activity import TaskActivity

        with self._repository.session_factory() as session:
            task = session.query(self._repository.model).filter_by(id=id).first()
            if not task:
                return None

            now = datetime.now(timezone.utc)

            # 1. Update task tracking
            task.started_at = now

            # 2. Insert Milestone Activity
            activity = TaskActivity(
                task_id=id,
                user_id=user_id,
                activity_type="started",
                content="Task successfully started!",
            )
            session.add(activity)

            # 3. Insert Progress Checkpoint
            checkpoint = TaskCheckpoint(
                task_id=id,
                reported_by=user_id,
                checkpoint_type="started",
                progress_pct=0,
            )
            session.add(checkpoint)

            session.commit()
            return self.get_by_id(id)

    def complete_task(self, id: str, user_id: str, completed_at: Any = None) -> Any:
        from datetime import datetime, timezone
        from app.model.task_checkpoint import TaskCheckpoint
        from app.model.task_activity import TaskActivity

        with self._repository.session_factory() as session:
            task = session.query(self._repository.model).filter_by(id=id).first()
            if not task:
                return None

            effective_done_at = (
                completed_at if completed_at else datetime.now(timezone.utc)
            )
            checkpoint_kind = "manual_end" if completed_at else "completed"

            # 1. Update Task status and actual finish
            task.completed_at = effective_done_at
            # Find the completed status ID dynamically from your table schema, or leave for endpoint layer to provide

            # 2. Activity
            activity = TaskActivity(
                task_id=id,
                user_id=user_id,
                activity_type=checkpoint_kind,
                content="Task marked as completed!",
            )
            session.add(activity)

            # 3. Insert Final Checkpoint
            checkpoint = TaskCheckpoint(
                task_id=id,
                reported_by=user_id,
                checkpoint_type=checkpoint_kind,
                progress_pct=100,
            )
            session.add(checkpoint)

            # 4. Auto-calculate actual_hours if not already set (or if logs exist)
            from app.model.task_time_log import TaskTimeLog
            from sqlalchemy import func

            total_logged = (
                session.query(func.sum(TaskTimeLog.hours))
                .filter(TaskTimeLog.task_id == id)
                .scalar()
                or 0.0
            )

            if total_logged > 0:
                task.actual_hours = float(total_logged)
            elif task.started_at and task.actual_hours == 0.0:
                duration = (
                    task.completed_at - task.started_at
                ).total_seconds() / 3600.0
                task.actual_hours = round(max(0.0, duration), 2)

            session.commit()
            return self.get_by_id(id)

    def get_task_activities(self, task_id: str):
        return self._repository.get_task_activities_raw(task_id)

    def create_comment(self, task_id: str, user_id: str, content: str):
        return self._repository.create_comment_activity(task_id, user_id, content)
