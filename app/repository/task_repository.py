from app.repository.base_repository import BaseRepository
from app.model.task import Task
from app.model.task_member import TaskMember
from app.model.task_activity import TaskActivity
from app.core.exceptions import NotFoundError


class TaskRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(session_factory, Task)

    def create(self, schema, acting_user_id: str = None, auto_commit=True):
        data = schema.model_dump() if hasattr(schema, "model_dump") else schema
        member_ids = data.pop("member_ids", []) or []

        from app.model.task_status import TaskStatus
        from datetime import datetime, timezone

        with self.session_factory() as session:
            # Auto-stamp life-cycle times on creation if explicit non-default status is chosen
            if "status_id" in data and data["status_id"]:
                new_status = (
                    session.query(TaskStatus).filter_by(id=data["status_id"]).first()
                )
                if new_status:
                    now_utc = datetime.now(timezone.utc)
                    # 1. Auto-stamp started_at if not default
                    if not data.get("started_at") and not new_status.is_default:
                        data["started_at"] = now_utc

                    # 2. Auto-stamp completed_at if status is completed
                    if new_status.is_completed:
                        if not data.get("completed_at"):
                            data["completed_at"] = now_utc
                            # Ensure start timestamp is valid
                            if not data.get("started_at"):
                                data["started_at"] = now_utc

            item = self.model(**data)
            session.add(item)
            session.flush()  # Ensure item has an ID before attaching members

            # 1. Add creator as Lead
            if acting_user_id:
                lead_member = TaskMember(
                    task_id=item.id, user_id=acting_user_id, role="lead"
                )
                session.add(lead_member)

            # 2. Add additional members, avoid duplicating the lead if included in user inputs
            for uid in member_ids:
                if uid == acting_user_id:
                    continue
                mbr = TaskMember(task_id=item.id, user_id=uid, role="member")
                session.add(mbr)

            if auto_commit:
                session.commit()
                session.refresh(item)

                # Index in Qdrant
                from app.utils.qdrant_helper import (
                    upsert_task_vector,
                    run_async_background,
                )

                run_async_background(
                    upsert_task_vector(
                        item.id, item.title, item.description, item.project_id
                    )
                )
            else:
                session.flush()
            return item

    def update(self, id, schema, auto_commit=True, eager=False, user_id=None):
        data = (
            schema.model_dump(exclude_none=True)
            if hasattr(schema, "model_dump")
            else schema
        )
        member_ids = data.pop("member_ids", None)
        with self.session_factory() as session:
            item = session.query(self.model).filter(self.model.id == id).first()
            if not item:
                raise NotFoundError(detail=f"not found id : {id}")

            # Check for field changes to record activity
            if user_id:
                tracked_fields = {
                    "status_id": "status",
                    "priority_id": "priority",
                    "type_id": "type",
                    "title": "title",
                    "due_date": "due_date",
                    "description": "description",
                    "phase_id": "phase",
                    "estimated_hours": "estimated_hours",
                }

                from app.model.task_status import TaskStatus
                from app.model.task_priority import TaskPriority
                from app.model.task_type import TaskType

                for f_key, label in tracked_fields.items():
                    if f_key in data and getattr(item, f_key) != data[f_key]:
                        old_raw = getattr(item, f_key)
                        new_raw = data[f_key]
                        
                        # Small safety to not create noise on null -> "" migrations etc.
                        old_v = str(old_raw) if old_raw is not None else None
                        new_v = str(new_raw) if new_raw is not None else None
                        
                        if old_v == new_v:
                            continue

                        # Lookup friendly names for relations instead of recording raw IDs
                        if f_key == "status_id":
                            old_v = item.status.name if item.status else old_v
                            new_entity = session.query(TaskStatus).filter_by(id=new_raw).first() if new_raw else None
                            new_v = new_entity.name if new_entity else new_v
                        elif f_key == "priority_id":
                            old_v = item.priority.name if item.priority else old_v
                            new_entity = session.query(TaskPriority).filter_by(id=new_raw).first() if new_raw else None
                            new_v = new_entity.name if new_entity else new_v
                        elif f_key == "type_id":
                            old_v = item.type.name if item.type else old_v
                            new_entity = session.query(TaskType).filter_by(id=new_raw).first() if new_raw else None
                            new_v = new_entity.name if new_entity else new_v

                        act_type = (
                            "status_change" if f_key == "status_id" else "field_change"
                        )

                        activity = TaskActivity(
                            task_id=id,
                            user_id=user_id,
                            activity_type=act_type,
                            field_name=label,
                            old_value=old_v,
                            new_value=new_v,
                        )
                        session.add(activity)

                # Member logging diff
                if member_ids is not None:
                    current_member_ids = {m.user_id for m in item.task_members}
                    new_member_ids = set(member_ids)
                    
                    added_uids = new_member_ids - current_member_ids
                    removed_uids = current_member_ids - new_member_ids

                    if added_uids or removed_uids:
                        from app.model.user import User
                        affected_uids = list(added_uids | removed_uids)
                        users = session.query(User).filter(User.id.in_(affected_uids)).all()
                        user_map = {u.id: u.name for u in users}
                        
                        for uid in added_uids:
                            u_name = user_map.get(uid, "Unknown User")
                            session.add(TaskActivity(
                                task_id=id,
                                user_id=user_id,
                                activity_type="member_add",
                                new_value=u_name,
                            ))
                        for uid in removed_uids:
                            u_name = user_map.get(uid, "Unknown User")
                            session.add(TaskActivity(
                                task_id=id,
                                user_id=user_id,
                                activity_type="member_remove",
                                old_value=u_name,
                            ))

            # Check if the status change specifically requires trigger
            if "status_id" in data and data["status_id"] != item.status_id:
                from app.model.task_status import TaskStatus
                from app.model.risk_snapshot import RiskSnapshot
                from datetime import datetime, timezone

                new_status = (
                    session.query(TaskStatus).filter_by(id=data["status_id"]).first()
                )
                if new_status:
                    now_utc = datetime.now(timezone.utc)
                    # 1. Auto-stamp started_at if transitioning out of default/inbox for first time
                    if not item.started_at and not new_status.is_default:
                        item.started_at = now_utc

                    # 2. Auto-stamp completed_at if transitioned to completion status
                    if new_status.is_completed:
                        if "completed_at" not in data or not data["completed_at"]:
                            item.completed_at = now_utc
                            # Also populate started_at if someone skips straight from Todo to Done
                            if not item.started_at:
                                item.started_at = now_utc

                    latest_snapshot = (
                        session.query(RiskSnapshot)
                        .filter_by(task_id=id)
                        .order_by(RiskSnapshot.created_at.desc())
                        .first()
                    )
                    if latest_snapshot:
                        latest_snapshot.actual_completed_at = now_utc
                        if latest_snapshot.predicted_completion_at:
                            diff = (
                                now_utc - latest_snapshot.predicted_completion_at
                            ).total_seconds() / 3600.0
                            latest_snapshot.prediction_error_hours = diff
                        elif item.estimated_hours is not None:
                            latest_snapshot.prediction_error_hours = (
                                item.actual_hours - item.estimated_hours
                            )
                        else:
                            latest_snapshot.prediction_error_hours = 0.0

            for key, value in data.items():
                setattr(item, key, value)

            if member_ids is not None:
                # Wipe and rebuild non-lead mappings or fully refresh
                # Easiest pattern: wipe all non-leads and replace with new set minus current user
                session.query(TaskMember).filter(
                    TaskMember.task_id == id, TaskMember.role != "lead"
                ).delete()
                for uid in member_ids:
                    # Check if already a lead
                    exists = (
                        session.query(TaskMember)
                        .filter_by(task_id=id, user_id=uid)
                        .first()
                    )
                    if not exists:
                        session.add(TaskMember(task_id=id, user_id=uid, role="member"))

            if auto_commit:
                session.commit()

                # Index in Qdrant
                from app.utils.qdrant_helper import (
                    upsert_task_vector,
                    run_async_background,
                )

                run_async_background(
                    upsert_task_vector(
                        item.id, item.title, item.description, item.project_id
                    )
                )
            return self.read_by_id(id, eager=eager)

    def read_by_options(self, schema, eager: bool = False):
        data = (
            schema.model_dump(exclude_none=True)
            if hasattr(schema, "model_dump")
            else schema
        )
        team_id = data.pop("team_id__eq", None)

        with self.session_factory() as session:
            from app.model.project import Project
            from app.utils.query_builder import dict_to_sqlalchemy_filter_options
            from sqlalchemy.orm import joinedload
            from app.core.config import settings

            ordering = data.get("ordering", settings.ORDERING)
            order_query = (
                getattr(self.model, ordering[1:]).desc()
                if ordering.startswith("-")
                else getattr(self.model, ordering).asc()
            )
            page = data.get("page", settings.PAGE)
            page_size = data.get("page_size", settings.PAGE_SIZE)

            filter_options = dict_to_sqlalchemy_filter_options(self.model, data)
            query = (
                session.query(self.model)
                .join(Project, Project.id == self.model.project_id)
                .filter(Project.is_deleted.is_(False))
            )

            if team_id:
                query = query.filter(Project.team_id == team_id)

            if eager:
                for eager_attr in getattr(self.model, "eagers", []):
                    query = query.options(joinedload(getattr(self.model, eager_attr)))

            filtered_query = query.filter(filter_options)
            query = filtered_query.order_by(order_query)

            if page_size == "all":
                results = query.all()
            else:
                results = query.limit(page_size).offset((page - 1) * page_size).all()

            total_count = filtered_query.count()
            return {
                "founds": results,
                "search_options": {
                    "page": page,
                    "page_size": page_size,
                    "ordering": ordering,
                    "total_count": total_count,
                },
            }

    def get_my_tasks_complex(
        self, user_id: str, user_member_ids: list[str], team_id: str | None = None
    ):
        with self.session_factory() as session:
            from sqlalchemy.orm import joinedload
            from app.model.project import Project

            query = (
                session.query(self.model)
                .join(Project, self.model.project_id == Project.id)
                .filter(
                    self.model.is_deleted.is_(False),
                    self.model.is_archived.is_(False),
                    Project.is_deleted.is_(False),
                )
            )

            if team_id:
                query = query.filter(Project.team_id == team_id)

            # Check if user is registered in the task_members table for this task
            query = query.filter(
                self.model.task_members.any(TaskMember.user_id == user_id)
            )

            for eager_attr in self.model.eagers:
                query = query.options(joinedload(getattr(self.model, eager_attr)))

            return query.order_by(self.model.id.desc()).all()

    def get_my_tasks_overview(
        self, user_id: str, user_member_ids: list[str], team_id: str | None = None, client_today=None
    ):
        from datetime import datetime, timezone

        tasks = self.get_my_tasks_complex(user_id, user_member_ids, team_id)

        if client_today is None:
            client_today_date = datetime.now(timezone.utc).date()
        else:
            client_today_date = client_today.date()

        in_progress = []
        upcoming = []
        overdue = []

        for t in tasks:
            if t.status and t.status.is_completed:
                continue

            is_overdue = False
            if t.due_date:
                if t.due_date.date() < client_today_date:
                    is_overdue = True

            if is_overdue:
                overdue.append(t)
                continue

            is_started = False
            if t.started_at:
                is_started = True
            elif t.status and t.status.name:
                name_low = t.status.name.lower()
                keywords = ["progress", "doing", "review", "đang", "thực hiện", "block"]
                if any(kw in name_low for kw in keywords):
                    is_started = True

            if is_started:
                in_progress.append(t)
            else:
                upcoming.append(t)

        return {
            "in_progress": in_progress,
            "upcoming": upcoming,
            "overdue": overdue
        }

    def get_user_completed_tasks_count(self, user_id: str, since) -> int:
        with self.session_factory() as session:
            from app.model.task_status import TaskStatus

            user_task_ids_q = session.query(TaskMember.task_id).filter(
                TaskMember.user_id == user_id
            )

            return (
                session.query(self.model)
                .join(TaskStatus, TaskStatus.id == self.model.status_id)
                .filter(
                    self.model.id.in_(user_task_ids_q),
                    TaskStatus.is_completed.is_(True),
                    self.model.updated_at >= since,
                    self.model.is_deleted.is_(False),
                )
                .count()
            )

    def get_user_collaborators_count(self, user_id: str, since) -> int:
        with self.session_factory() as session:
            user_task_ids_q = session.query(TaskMember.task_id).filter(
                TaskMember.user_id == user_id
            )

            active_task_ids_q = session.query(self.model.id).filter(
                self.model.id.in_(user_task_ids_q),
                self.model.updated_at >= since,
                self.model.is_deleted.is_(False),
            )

            other_user_ids_q = (
                session.query(TaskMember.user_id)
                .filter(
                    TaskMember.task_id.in_(active_task_ids_q),
                    TaskMember.user_id != user_id,
                )
                .distinct()
            )

            return other_user_ids_q.count()

    def get_project_task_stats_raw(self, project_id: str, date_from, date_to):
        with self.session_factory() as session:
            from sqlalchemy import func
            from app.model.task_priority import TaskPriority
            from app.model.task_status import TaskStatus
            from app.model.task_type import TaskType

            shared_filters = [
                self.model.project_id == project_id,
                self.model.is_deleted.is_(False),
                self.model.is_archived.is_(False),
                self.model.updated_at >= date_from,
                self.model.updated_at < date_to,
            ]

            priority_rows = (
                session.query(
                    TaskPriority.id,
                    TaskPriority.name,
                    TaskPriority.color,
                    func.count(self.model.id),
                )
                .join(self.model, self.model.priority_id == TaskPriority.id)
                .filter(*shared_filters)
                .group_by(TaskPriority.id, TaskPriority.name, TaskPriority.color)
                .all()
            )

            status_rows = (
                session.query(
                    TaskStatus.id,
                    TaskStatus.name,
                    TaskStatus.color,
                    func.count(self.model.id),
                )
                .join(self.model, self.model.status_id == TaskStatus.id)
                .filter(*shared_filters)
                .group_by(TaskStatus.id, TaskStatus.name, TaskStatus.color)
                .all()
            )

            type_rows = (
                session.query(
                    TaskType.id,
                    TaskType.name,
                    TaskType.color,
                    func.count(self.model.id),
                )
                .join(self.model, self.model.type_id == TaskType.id)
                .filter(*shared_filters)
                .group_by(TaskType.id, TaskType.name, TaskType.color)
                .all()
            )

            return priority_rows, status_rows, type_rows

    def get_project_risk_data(self, project_id: str):
        with self.session_factory() as session:
            from app.model.risk_snapshot import RiskSnapshot

            active_tasks = (
                session.query(self.model)
                .filter(
                    self.model.project_id == project_id,
                    self.model.is_deleted.is_(False),
                    self.model.is_archived.is_(False),
                )
                .all()
            )

            if not active_tasks:
                return [], []

            task_ids = [t.id for t in active_tasks]
            snapshots = (
                session.query(RiskSnapshot)
                .filter(RiskSnapshot.task_id.in_(task_ids))
                .order_by(RiskSnapshot.created_at.desc())
                .all()
            )

            return active_tasks, snapshots

    def get_recent_updates_raw(self, project_id: str, limit: int):
        with self.session_factory() as session:
            from app.model.task_activity import TaskActivity
            from app.model.task_status import TaskStatus
            from sqlalchemy.orm import joinedload

            activities = (
                session.query(TaskActivity)
                .join(self.model, self.model.id == TaskActivity.task_id)
                .filter(
                    self.model.project_id == project_id,
                    TaskActivity.activity_type == "status_change"
                )
                .options(joinedload(TaskActivity.task), joinedload(TaskActivity.user))
                .order_by(TaskActivity.created_at.desc())
                .limit(limit)
                .all()
            )

            status_ids = set()
            for activity in activities:
                if activity.old_value:
                    status_ids.add(activity.old_value)
                if activity.new_value:
                    status_ids.add(activity.new_value)

            status_map = {}
            if status_ids:
                statuses = (
                    session.query(TaskStatus)
                    .filter(
                        TaskStatus.project_id == project_id,
                        (
                            (TaskStatus.id.in_(status_ids)) |
                            (TaskStatus.name.in_(status_ids))
                        )
                    )
                    .all()
                )
                for s in statuses:
                    info = {"name": s.name, "color": s.color}
                    status_map[s.id] = info
                    status_map[s.name] = info

            return activities, status_map

    def get_tasks_by_ids(self, task_ids: list[str]):
        with self.session_factory() as session:
            return session.query(self.model).filter(self.model.id.in_(task_ids)).all()

    def get_active_task_ids_by_project(self, project_id: str) -> list[str]:
        with self.session_factory() as session:
            from app.model.task_status import TaskStatus

            tasks = (
                session.query(self.model)
                .join(TaskStatus, TaskStatus.id == self.model.status_id)
                .filter(
                    self.model.project_id == project_id,
                    self.model.is_deleted.is_(False),
                    self.model.is_archived.is_(False),
                    TaskStatus.is_completed.is_(False),
                )
                .all()
            )
            return [t.id for t in tasks]

    def create_task_assignment_notifications(self, task_id: str, member_ids: list[str]):
        if not member_ids:
            return
        with self.session_factory() as session:
            from sqlalchemy.orm import joinedload
            from app.model.task import Task
            from app.model.project import Project
            from app.model.notification import (
                Notification,
                NotificationType,
                NotificationStatus,
            )

            task = (
                session.query(self.model)
                .options(joinedload(Task.project).joinedload(Project.team))
                .filter(self.model.id == task_id)
                .first()
            )
            if not task:
                return

            project = task.project
            team = project.team if project else None

            for m_uid in member_ids:
                n = Notification(
                    user_id=m_uid,
                    title="New Task Assignment",
                    content=f"You have been added to task '{task.title}' in project '{project.name if project else 'Unknown'}' ({team.name if team else 'Unknown Team'})",
                    type=NotificationType.TASK_ASSIGNED,
                    status=NotificationStatus.ACTIVE,
                    is_read=False,
                    resource_id=task.id,
                    resource_type="task",
                    data={
                        "task_id": task.id,
                        "task_title": task.title,
                        "project_id": task.project_id,
                        "project_name": project.name if project else None,
                        "team_id": project.team_id if project else None,
                        "team_name": team.name if team else None,
                    },
                )
                session.add(n)
            session.commit()

    def get_task_member_ids(self, task_id: str) -> set[str]:
        with self.session_factory() as session:
            task = session.query(self.model).filter_by(id=task_id).first()
            if task:
                return {m.user_id for m in task.task_members}
            return set()

    def get_task_activities_raw(self, task_id: str):
        with self.session_factory() as session:
            from app.model.task_activity import TaskActivity
            from sqlalchemy.orm import joinedload

            return (
                session.query(TaskActivity)
                .filter(TaskActivity.task_id == task_id)
                .options(joinedload(TaskActivity.user))
                .order_by(TaskActivity.created_at.desc())
                .all()
            )

    def create_comment_activity(self, task_id: str, user_id: str, content: str):
        with self.session_factory() as session:
            from app.model.task_activity import TaskActivity

            activity = TaskActivity(
                task_id=task_id,
                user_id=user_id,
                activity_type="comment",
                content=content,
            )
            session.add(activity)
            session.commit()
            session.refresh(activity)

            # Load relationship before returning
            from sqlalchemy.orm import joinedload

            return (
                session.query(TaskActivity)
                .filter_by(id=activity.id)
                .options(joinedload(TaskActivity.user))
                .first()
            )

    def get_projects_stats(self, project_ids: list[str]):
        if not project_ids:
            return {}

        from app.model.task_status import TaskStatus
        from app.model.task_activity import TaskActivity
        from sqlalchemy import func, cast, Integer
        from datetime import datetime, timedelta, timezone

        with self.session_factory() as session:
            # 1. Total and Completed tasks count
            counts_query = (
                session.query(
                    self.model.project_id,
                    func.count(self.model.id).label("total"),
                    func.sum(cast(TaskStatus.is_completed, Integer)).label("completed")
                )
                .join(TaskStatus, TaskStatus.id == self.model.status_id)
                .filter(
                    self.model.project_id.in_(project_ids),
                    self.model.is_deleted.is_(False),
                    self.model.is_archived.is_(False)
                )
                .group_by(self.model.project_id)
                .all()
            )

            stats_map = {
                row.project_id: {
                    "total_tasks": row.total,
                    "completed_tasks": int(row.completed or 0),
                    "weekly_activity": [0] * 7
                }
                for row in counts_query
            }

            # Ensure all requested projects exist in stats_map
            for pid in project_ids:
                if pid not in stats_map:
                    stats_map[pid] = {
                        "total_tasks": 0,
                        "completed_tasks": 0,
                        "weekly_activity": [0] * 7
                    }

            # 2. Daily Activity (TaskActivity count)
            now = datetime.now(timezone.utc)
            seven_days_ago = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=6)

            activity_query = (
                session.query(
                    self.model.project_id,
                    TaskActivity.created_at
                )
                .join(TaskActivity, TaskActivity.task_id == self.model.id)
                .filter(
                    self.model.project_id.in_(project_ids),
                    TaskActivity.created_at >= seven_days_ago
                )
                .all()
            )

            # Group activities by day relative to today
            for pid, created_at in activity_query:
                delta_days = (created_at.date() - seven_days_ago.date()).days
                if 0 <= delta_days < 7:
                    if pid in stats_map:
                        stats_map[pid]["weekly_activity"][delta_days] += 1

            return stats_map

    def get_teams_stats(self, team_ids: list[str]):
        if not team_ids:
            return {}

        from app.model.task_status import TaskStatus
        from app.model.task_activity import TaskActivity
        from app.model.project import Project
        from sqlalchemy import func, cast, Integer
        from datetime import datetime, timedelta, timezone

        with self.session_factory() as session:
            # 1. Count totals
            counts_query = (
                session.query(
                    Project.team_id,
                    func.count(self.model.id).label("total"),
                    func.sum(cast(TaskStatus.is_completed, Integer)).label("completed")
                )
                .join(Project, Project.id == self.model.project_id)
                .join(TaskStatus, TaskStatus.id == self.model.status_id)
                .filter(
                    Project.team_id.in_(team_ids),
                    self.model.is_deleted.is_(False),
                    self.model.is_archived.is_(False),
                    Project.is_deleted.is_(False)
                )
                .group_by(Project.team_id)
                .all()
            )

            stats_map = {
                row.team_id: {
                    "total_tasks": row.total,
                    "completed_tasks": int(row.completed or 0),
                    "weekly_activity": [0] * 7
                }
                for row in counts_query
            }

            for tid in team_ids:
                if tid not in stats_map:
                    stats_map[tid] = {
                        "total_tasks": 0,
                        "completed_tasks": 0,
                        "weekly_activity": [0] * 7
                    }

            # 2. Activity
            now = datetime.now(timezone.utc)
            seven_days_ago = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=6)

            activity_query = (
                session.query(
                    Project.team_id,
                    TaskActivity.created_at
                )
                .join(self.model, self.model.id == TaskActivity.task_id)
                .join(Project, Project.id == self.model.project_id)
                .filter(
                    Project.team_id.in_(team_ids),
                    TaskActivity.created_at >= seven_days_ago,
                    Project.is_deleted.is_(False)
                )
                .all()
            )

            for tid, created_at in activity_query:
                delta_days = (created_at.date() - seven_days_ago.date()).days
                if 0 <= delta_days < 7:
                    if tid in stats_map:
                        stats_map[tid]["weekly_activity"][delta_days] += 1

            return stats_map
