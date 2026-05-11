from datetime import datetime, timedelta
from datetime import timezone as pytimezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.model.project import Project
from app.model.project_member import ProjectMember
from app.model.task import Task
from app.model.task_checkpoint import TaskCheckpoint
from app.model.task_priority import TaskPriority
from app.model.task_status import TaskStatus
from app.model.task_type import TaskType
from app.model.team import Team
from app.model.team_member import TeamMember
from app.model.user import User
from app.model.work_schedule import WorkSchedule
from app.model.task_member import TaskMember


class TestingService:
    @staticmethod
    def generate_mock_project_data(
        db: Session,
        current_user: User,
        user_id: str | None = None,
        project_name: str = "Enterprise ERP Core Platform",
        timezone: str = "Asia/Ho_Chi_Minh",
    ):
        # Resolve target user
        target_user = current_user
        if user_id:
            found_user = db.get(User, user_id)
            if found_user:
                target_user = found_user

        # 1. Create Mock Team
        team = Team(
            name=f"Enterprise Cloud Dev Team ({target_user.name})",
            description="Realistic mock team for AI Agent testing",
            owner_id=target_user.id,
        )
        db.add(team)
        db.flush()

        lead_team_member = TeamMember(
            team_id=team.id,
            user_id=target_user.id,
            role="owner",
        )
        db.add(lead_team_member)
        db.flush()

        # 2. Create Project
        project = Project(
            team_id=team.id,
            name=project_name,
            description="Corporate ERP system migration to cloud",
            timezone=timezone,
        )
        db.add(project)
        db.flush()

        # 3. Statuses
        statuses = {}
        status_configs = [
            {
                "name": "Backlog",
                "color": "#6b7280",
                "is_default": True,
                "is_completed": False,
                "order": 1.0,
            },
            {
                "name": "In Progress",
                "color": "#3b82f6",
                "is_default": False,
                "is_completed": False,
                "order": 2.0,
            },
            {
                "name": "Blocked",
                "color": "#ef4444",
                "is_default": False,
                "is_completed": False,
                "order": 3.0,
            },
            {
                "name": "Completed",
                "color": "#10b981",
                "is_default": False,
                "is_completed": True,
                "order": 4.0,
            },
        ]
        for config in status_configs:
            s_obj = TaskStatus(
                project_id=project.id,
                name=config["name"],
                color=config["color"],
                is_default=config["is_default"],
                is_completed=config["is_completed"],
                order=config["order"],
            )
            db.add(s_obj)
            db.flush()
            statuses[config["name"]] = s_obj

        # 4. Priorities
        priorities = {}
        priority_configs = [
            {
                "name": "Low",
                "color": "#6b7280",
                "level": 1,
                "is_default": False,
                "order": 1.0,
            },
            {
                "name": "Medium",
                "color": "#3b82f6",
                "level": 2,
                "is_default": True,
                "order": 2.0,
            },
            {
                "name": "High",
                "color": "#f97316",
                "level": 3,
                "is_default": False,
                "order": 3.0,
            },
            {
                "name": "Critical",
                "color": "#ef4444",
                "level": 4,
                "is_default": False,
                "order": 4.0,
            },
        ]
        for config in priority_configs:
            p_obj = TaskPriority(
                project_id=project.id,
                name=config["name"],
                color=config["color"],
                level=config["level"],
                is_default=config["is_default"],
                order=config["order"],
            )
            db.add(p_obj)
            db.flush()
            priorities[config["name"]] = p_obj

        # 5. Types
        types = {}
        type_configs = [
            {"name": "Task", "color": "#3b82f6", "is_default": True, "order": 1.0},
            {"name": "Story", "color": "#10b981", "is_default": False, "order": 2.0},
            {"name": "Bug", "color": "#ef4444", "is_default": False, "order": 3.0},
        ]
        for config in type_configs:
            t_obj = TaskType(
                project_id=project.id,
                name=config["name"],
                color=config["color"],
                is_default=config["is_default"],
                order=config["order"],
            )
            db.add(t_obj)
            db.flush()
            types[config["name"]] = t_obj

        # 6. Project Member
        lead_member = ProjectMember(
            project_id=project.id, user_id=target_user.id, role="manager"
        )
        db.add(lead_member)
        db.flush()

        # 7. Users
        mock_dev_email = f"dev_{team.id[:8]}@agentick.com"
        mock_dev = db.scalars(select(User).where(User.email == mock_dev_email)).first()
        if not mock_dev:
            mock_dev = User(
                email=mock_dev_email,
                name="Nguyen Van Dev",
                hashed_password=get_password_hash("password123"),
                user_token=f"token_{team.id[:8]}_dev",
                is_active=True,
            )
            db.add(mock_dev)
            db.flush()

        mock_tester_email = f"tester_{team.id[:8]}@agentick.com"
        mock_tester = db.scalars(
            select(User).where(User.email == mock_tester_email)
        ).first()
        if not mock_tester:
            mock_tester = User(
                email=mock_tester_email,
                name="Tran Thi Tester",
                hashed_password=get_password_hash("password123"),
                user_token=f"token_{team.id[:8]}_tester",
                is_active=True,
            )
            db.add(mock_tester)
            db.flush()

        # Team Members
        db.add(TeamMember(team_id=team.id, user_id=mock_dev.id, role="member"))
        db.add(TeamMember(team_id=team.id, user_id=mock_tester.id, role="member"))
        db.flush()

        # Project Members
        dev_member = ProjectMember(
            project_id=project.id, user_id=mock_dev.id, role="member"
        )
        tester_member = ProjectMember(
            project_id=project.id, user_id=mock_tester.id, role="member"
        )
        db.add(dev_member)
        db.add(tester_member)
        db.flush()

        # 8. Schedules
        for user_id in [mock_dev.id, mock_tester.id]:
            for d in range(7):
                is_off = d in [5, 6]
                sched = WorkSchedule(
                    team_id=team.id,
                    user_id=user_id,
                    day_of_week=d,
                    start_time="09:00" if not is_off else None,
                    end_time="18:00" if not is_off else None,
                    is_off=is_off,
                )
                db.add(sched)
        db.flush()

        # 9. Tasks
        # Normalize times to clean day start / day end to avoid weird Gantt offsets (e.g., 10:27 PM)
        now = datetime.now(pytimezone.utc)
        base_start = now.replace(
            hour=9, minute=0, second=0, microsecond=0
        )  # 9 AM standard start
        base_eod = now.replace(
            hour=23, minute=59, second=0, microsecond=0
        )  # EOD standard deadline

        task_payment = Task(
            project_id=project.id,
            title="Implement Stripe Payment Gateway Integration",
            description="Integrate Stripe Checkout and billing webhook callbacks.",
            status_id=statuses["In Progress"].id,
            type_id=types["Task"].id,
            priority_id=priorities["High"].id,
            estimated_hours=20.0,
            actual_hours=28.0,
            started_at=base_start - timedelta(days=1),
            due_date=base_eod + timedelta(days=1),
        )
        db.add(task_payment)
        db.flush()
        db.add(TaskMember(task_id=task_payment.id, user_id=target_user.id, role="lead"))
        db.add(TaskMember(task_id=task_payment.id, user_id=mock_dev.id, role="member"))

        task_k8s = Task(
            project_id=project.id,
            title="Setup Production Kubernetes Cluster & Ingress",
            description="Provision AWS EKS cluster, set up Cert-Manager and Nginx Ingress.",
            status_id=statuses["Blocked"].id,
            type_id=types["Task"].id,
            priority_id=priorities["Critical"].id,
            estimated_hours=16.0,
            actual_hours=4.0,
            started_at=base_start - timedelta(days=2),
            due_date=base_eod + timedelta(days=2),
        )
        db.add(task_k8s)
        db.flush()
        db.add(TaskMember(task_id=task_k8s.id, user_id=target_user.id, role="lead"))
        db.add(TaskMember(task_id=task_k8s.id, user_id=mock_dev.id, role="member"))

        task_db = Task(
            project_id=project.id,
            title="Optimize ERP Slow Database Queries",
            status_id=statuses["In Progress"].id,
            type_id=types["Task"].id,
            priority_id=priorities["Medium"].id,
            estimated_hours=8.0,
            actual_hours=2.0,
            started_at=base_start - timedelta(hours=12),
            due_date=base_eod + timedelta(days=3),
        )
        db.add(task_db)
        db.flush()
        db.add(TaskMember(task_id=task_db.id, user_id=target_user.id, role="lead"))
        db.add(TaskMember(task_id=task_db.id, user_id=mock_dev.id, role="member"))

        task_auth = Task(
            project_id=project.id,
            title="Refactor OAuth Middleware & Token Caching",
            status_id=statuses["In Progress"].id,
            type_id=types["Task"].id,
            priority_id=priorities["High"].id,
            estimated_hours=12.0,
            actual_hours=1.0,
            started_at=base_start - timedelta(hours=6),
            due_date=base_eod + timedelta(days=4),
        )
        db.add(task_auth)
        db.flush()
        db.add(TaskMember(task_id=task_auth.id, user_id=target_user.id, role="lead"))
        db.add(TaskMember(task_id=task_auth.id, user_id=mock_dev.id, role="member"))

        task_missing_est = Task(
            project_id=project.id,
            title="[Test Phase 2] Stripe API Webhook Security Verification",
            status_id=statuses["In Progress"].id,
            type_id=types["Task"].id,
            priority_id=priorities["High"].id,
            estimated_hours=None,
            actual_hours=0.0,
            started_at=base_start - timedelta(hours=1),
            due_date=base_eod + timedelta(days=2),
        )
        db.add(task_missing_est)
        db.flush()
        db.add(
            TaskMember(task_id=task_missing_est.id, user_id=target_user.id, role="lead")
        )
        db.add(
            TaskMember(task_id=task_missing_est.id, user_id=mock_dev.id, role="member")
        )

        task_stale_chk = Task(
            project_id=project.id,
            title="[Test Phase 2] Docker Compose Local Cache Tuning",
            status_id=statuses["In Progress"].id,
            type_id=types["Task"].id,
            priority_id=priorities["Medium"].id,
            estimated_hours=8.0,
            actual_hours=1.0,
            started_at=base_start - timedelta(days=2),
            due_date=base_eod + timedelta(days=2),
            updated_at=now - timedelta(hours=26),
        )
        db.add(task_stale_chk)
        db.flush()
        db.add(
            TaskMember(task_id=task_stale_chk.id, user_id=target_user.id, role="lead")
        )
        db.add(
            TaskMember(task_id=task_stale_chk.id, user_id=mock_dev.id, role="member")
        )
        db.flush()

        # 🆕 EXPLICIT TEST CASE: Silent Risk (No started_at, deadline < 2 days)
        task_silent_risk = Task(
            project_id=project.id,
            title="[Test Scenario] CRITICAL: Database Replica Configuration",
            description="Task must trigger Silent Risk penalty (+0.3) because it has NOT started yet.",
            status_id=statuses[
                "In Progress"
            ].id,  # User technically moved it here but didn't press START
            type_id=types["Task"].id,
            priority_id=priorities["Critical"].id,
            estimated_hours=10.0,
            actual_hours=0.0,
            started_at=None,  # 🚨 CRITICAL TRIGGER for new logic
            due_date=base_eod + timedelta(hours=30),  # Near future EOD-ish
        )
        db.add(task_silent_risk)
        db.flush()
        db.add(
            TaskMember(task_id=task_silent_risk.id, user_id=target_user.id, role="lead")
        )
        db.add(
            TaskMember(task_id=task_silent_risk.id, user_id=mock_dev.id, role="member")
        )
        db.flush()

        # 10. Checkpoints
        db.add(
            TaskCheckpoint(
                task_id=task_payment.id,
                reported_by=mock_dev.id,
                progress_pct=40,
                remaining_hours=12.0,
                is_blocked=False,
            )
        )
        db.add(
            TaskCheckpoint(
                task_id=task_k8s.id,
                reported_by=mock_dev.id,
                progress_pct=10,
                remaining_hours=14.0,
                is_blocked=True,
                blocked_reason="AWS cloud resource quota exceeded. Pending enterprise account approval.",
            )
        )
        db.commit()

        return {
            "team_id": team.id,
            "project_id": project.id,
            "project_name": project.name,
            "timezone": project.timezone,
            "members": [
                {"name": target_user.name, "role": "manager"},
                {"name": "Nguyen Van Dev", "role": "member", "email": mock_dev_email},
                {
                    "name": "Tran Thi Tester",
                    "role": "member",
                    "email": mock_tester_email,
                },
            ],
            "tasks": [
                {
                    "id": task_payment.id,
                    "title": task_payment.title,
                    "estimated": task_payment.estimated_hours,
                    "actual": task_payment.actual_hours,
                },
                {
                    "id": task_k8s.id,
                    "title": task_k8s.title,
                    "estimated": task_k8s.estimated_hours,
                    "actual": task_k8s.actual_hours,
                },
                {"id": task_db.id, "title": task_db.title},
                {"id": task_auth.id, "title": task_auth.title},
                {"id": task_missing_est.id, "title": task_missing_est.title},
                {"id": task_stale_chk.id, "title": task_stale_chk.title},
                {"id": task_silent_risk.id, "title": task_silent_risk.title},
            ],
        }

    @staticmethod
    async def trigger_morning_scan_now(db: Session):
        """
        Highly optimized Forced Morning scan logic using Async Concurrency.
        Processes tasks in parallel bypassing serialized blocking, while enforcing
        a rate-limit safety semaphore.
        """
        import asyncio

        from sqlalchemy import select
        from sqlalchemy.orm import joinedload

        from app.model.task import Task
        from app.services.risk_analysis_service import RiskAnalysisService

        from app.core.dependencies import get_database

        tasks = db.scalars(
            select(Task)
            .options(joinedload(Task.project))
            .where(Task.is_archived.is_(False))
            .where(Task.is_deleted.is_(False))
        ).all()

        db_factory = get_database()

        # Enforce maximum of 5 concurrent requests to OpenRouter to avoid instant rate bans
        sem = asyncio.Semaphore(5)

        async def process_single_task(task_obj):
            status_name = task_obj.status.name.lower() if task_obj.status else ""
            if status_name in ["done", "completed"]:
                return None

            async with sem:
                # CRITICAL FIX: Use completely isolated DB Session for concurrent async execution
                with db_factory.session() as local_db:
                    try:
                        local_analyzer = RiskAnalysisService(local_db)
                        snapshot = await local_analyzer.analyze_task(task_obj.id)
                        return {
                            "task_id": task_obj.id,
                            "task_title": task_obj.title,
                            "risk_score": snapshot.risk_score,
                        }
                    except Exception as ex:
                        return {"task_id": task_obj.id, "error": str(ex)}

        # Trigger dynamic parallel pipeline
        raw_results = await asyncio.gather(*[process_single_task(t) for t in tasks])

        # Filter out skipped tasks and return
        return [r for r in raw_results if r is not None]

    @staticmethod
    async def trigger_evening_summary_now(db: Session, project_id: str | None = None):
        """
        Forced Evening summary email dispatcher, bypassing hour constraints.
        Sends a daily digest email instantly for demo purposes.
        """
        import os
        import smtplib
        from datetime import date
        from email.message import EmailMessage

        from sqlalchemy import func, select
        from sqlalchemy.orm import joinedload

        from app.core.config import configs
        from app.model.project import Project
        from app.model.team import Team
        from app.model.risk_snapshot import RiskSnapshot
        from app.model.task import Task

        today = date.today()
        query = (
            select(Project)
            .options(joinedload(Project.team).joinedload(Team.owner))
            .where(Project.is_deleted.is_(False))
        )

        if project_id:
            query = query.where(Project.id == project_id)

        projects = db.scalars(query).all()
        sent_reports = []

        for project in projects:
            snapshots = db.scalars(
                select(RiskSnapshot)
                .options(joinedload(RiskSnapshot.task))
                .join(Task, Task.id == RiskSnapshot.task_id)
                .where(Task.project_id == project.id)
                .where(func.date(RiskSnapshot.created_at) == today)
                .where(RiskSnapshot.risk_score >= 0.5)
                .order_by(RiskSnapshot.risk_score.desc())
            ).all()

            if not snapshots:
                continue

            # Dynamically resolve Team Lead / Owner email
            recipient_email = None
            if project.team and project.team.owner and project.team.owner.email:
                recipient_email = project.team.owner.email

            # Final safe fallback chain
            final_recipient = (
                recipient_email or os.getenv("TEAM_LEAD_EMAIL") or configs.SMTP_USER
            )
            if not final_recipient:
                continue

            report_title = f"📋 [DEMO] Daily Risk Digest - {project.name} - {today.strftime('%Y-%m-%d')}"
            html_content = "<html><body style='font-family: sans-serif;'>"
            html_content += f"<h2>🚀 Project Risk Report for {project.name}</h2>"
            html_content += (
                "<p>The following tasks exceeded the 0.5 Risk Threshold today:</p>"
            )
            html_content += "<table border='1' cellpadding='10' cellspacing='0' style='border-collapse: collapse;'><thead><tr style='background:#f0f0f0;'><th>Task</th><th>Risk Score</th><th>Status</th></tr></thead><tbody>"

            for snap in snapshots:
                lvl_color = "#ef4444" if snap.risk_score >= 0.8 else "#f59e0b"
                html_content += f"<tr><td>{snap.task.title}</td><td style='color:{lvl_color}; font-weight:bold;'>{snap.risk_score}</td><td>{snap.risk_level.upper()}</td></tr>"
            html_content += "</tbody></table>"
            html_content += "<p><br/><i>Generated by Agentick AI Intelligence Agent.</i></p></body></html>"

            msg = EmailMessage()
            msg["Subject"] = report_title
            msg["From"] = f"{configs.EMAILS_FROM_NAME} <{configs.SMTP_USER}>"
            msg["To"] = final_recipient
            msg.add_alternative(html_content, subtype="html")

            print(
                f"DEMO DISPATCHER: Attempting report send to {final_recipient} for project {project.name}"
            )

            if configs.SMTP_USER and configs.SMTP_PASSWORD:
                try:
                    server = smtplib.SMTP(configs.SMTP_HOST, configs.SMTP_PORT)
                    server.starttls()
                    server.login(configs.SMTP_USER, configs.SMTP_PASSWORD)
                    server.send_message(msg)
                    server.quit()
                    sent_reports.append(
                        {
                            "project_id": project.id,
                            "status": f"email_sent_to_{final_recipient}",
                        }
                    )
                    print(
                        f"DEMO DISPATCHER SUCCESS: Email delivered to {final_recipient}"
                    )
                except Exception as e:
                    sent_reports.append(
                        {"project_id": project.id, "status": f"error: {str(e)}"}
                    )
                    print(f"DEMO DISPATCHER FAILED: {e}")
            else:
                sent_reports.append(
                    {"project_id": project.id, "status": "no_smtp_creds"}
                )

        return sent_reports
