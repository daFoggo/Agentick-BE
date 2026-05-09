from datetime import datetime, timedelta
from datetime import timezone as pytimezone

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy import select

from app.core.dependencies import get_current_active_user, get_db
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
from app.schema.base_schema import ResponseSchema
from app.services.risk_analysis_service import RiskAnalysisService

router = APIRouter(prefix="/agent", tags=["agent"])


def get_risk_analysis_service(db=Depends(get_db)) -> RiskAnalysisService:
    return RiskAnalysisService(db=db)


@router.post("/tasks/{task_id}/risk-analyses", response_model=ResponseSchema)
async def analyze_task_risk(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RiskAnalysisService = Depends(get_risk_analysis_service),
):
    result = await service.analyze_task(task_id=task_id)
    return ResponseSchema(
        data={
            "task_id": result.task_id,
            "risk_score": result.risk_score,
            "risk_level": result.risk_level,
            "recommendation": result.recommendation,
            "signals": result.signals,
            "alert_sent": result.alert_sent,
        },
        message="Risk snapshot generated successfully",
    )


@router.post("/outreaches", response_model=ResponseSchema)
async def trigger_agent_outreach(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
):
    """
    Trigger the programmatic stale task and missing data detection cycle,
    then compose and send personalized outreach emails via Gmail in the background.
    """
    from app.core.dependencies import get_database
    from app.services.agent_outreach_service import AgentOutreachService

    async def run_outreach():
        try:
            with get_database().session() as session:
                service = AgentOutreachService(db=session)
                await service.run_outreach_cycle()
        except Exception as e:
            print(f"Error running outreach cycle in background: {e}")

    background_tasks.add_task(run_outreach)
    return ResponseSchema(
        data={"status": "queued"},
        message="Agent outreach cycle has been queued in background successfully.",
    )


@router.post("/projects/{project_id}/risk-analyses", response_model=ResponseSchema)
async def analyze_project_risk(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """
    Trigger risk analysis for all active tasks in a project in parallel.
    Uses separate concurrency-safe DB sessions for each task to avoid transaction conflicts.
    """
    from sqlalchemy.orm import joinedload
    import asyncio
    from app.core.dependencies import get_database

    tasks = (
        db.query(Task)
        .options(joinedload(Task.status))
        .filter(
            Task.project_id == project_id,
            Task.is_deleted.is_(False),
            Task.is_archived.is_(False),
        )
        .all()
    )

    active_task_ids = []
    for task in tasks:
        status_name = task.status.name.lower() if task.status else ""
        if status_name not in ["done", "completed"]:
            active_task_ids.append(task.id)

    if not active_task_ids:
        return ResponseSchema(
            data={"analyzed_count": 0}, message="No active tasks to analyze"
        )

    async def analyze_single_task_safely(task_id: str):
        try:
            with get_database().session() as session:
                task_service = RiskAnalysisService(db=session)
                await task_service.analyze_task(task_id=task_id)
            return True
        except Exception as e:
            print(f"Error analyzing task {task_id}: {e}")
            return False

    # Run all analyses in parallel!
    results = await asyncio.gather(
        *(analyze_single_task_safely(tid) for tid in active_task_ids)
    )
    count = sum(1 for r in results if r)

    return ResponseSchema(
        data={"analyzed_count": count},
        message=f"Analyzed {count} tasks in parallel successfully",
    )


@router.post("/test-data", response_model=ResponseSchema)
async def generate_test_data(
    user_id: str | None = None,
    project_name: str = "Enterprise ERP Core Platform",
    timezone: str = "Asia/Ho_Chi_Minh",
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    # Resolve target user
    target_user = current_user
    if user_id:
        found_user = db.get(User, user_id)
        if found_user:
            target_user = found_user

    # 1. Create Mock Team owned by Target User
    team = Team(
        name=f"Enterprise Cloud Dev Team ({target_user.name})",
        description="Realistic mock team for AI Agent testing",
        owner_id=target_user.id,
    )
    db.add(team)
    db.flush()

    # Create TeamMember for Target User to make it visible on Frontend
    lead_team_member = TeamMember(
        team_id=team.id,
        user_id=target_user.id,
        role="owner",
    )
    db.add(lead_team_member)
    db.flush()

    # 2. Create Mock Project inside the Team
    project = Project(
        team_id=team.id,
        name=project_name,
        description="Corporate ERP system migration to cloud",
        timezone=timezone,
    )
    db.add(project)
    db.flush()

    # 3. Create Project-specific task statuses
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

    # 4. Create Project-specific task priorities
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

    # 5. Create Project-specific task types
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

    # 6. Create Project Lead Member (The Target User)
    lead_member = ProjectMember(
        project_id=project.id, user_id=target_user.id, role="manager"
    )
    db.add(lead_member)
    db.flush()

    # 7. Create/Find Mock Developer and Tester Users
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

    # Add Team Members
    dev_team_member = TeamMember(
        team_id=team.id,
        user_id=mock_dev.id,
        role="member",
    )
    tester_team_member = TeamMember(
        team_id=team.id,
        user_id=mock_tester.id,
        role="member",
    )
    db.add(dev_team_member)
    db.add(tester_team_member)
    db.flush()

    # Add Project Members
    dev_member = ProjectMember(
        project_id=project.id, user_id=mock_dev.id, role="member"
    )
    tester_member = ProjectMember(
        project_id=project.id, user_id=mock_tester.id, role="member"
    )
    db.add(dev_member)
    db.add(tester_member)
    db.flush()

    # 8. Create WorkSchedules for Dev and Tester (Mon-Fri 09:00 - 18:00, Weekends off)
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

    # 9. Create 4 Realistic Tasks to Simulate Real corporate risk constraints
    now = datetime.now(pytimezone.utc)

    # Task 1: Highly Overdue & High-Risk Task (estimated < actual + remaining)
    task_payment = Task(
        project_id=project.id,
        title="Implement Stripe Payment Gateway Integration",
        description="Integrate Stripe Checkout and billing webhook callbacks.",
        status_id=statuses["In Progress"].id,
        type_id=types["Task"].id,
        priority_id=priorities["High"].id,
        assigner_id=lead_member.id,
        estimated_hours=20.0,
        actual_hours=28.0,  # Over estimated limit!
        due_date=now + timedelta(days=1),  # Deadline tomorrow!
    )
    task_payment.assignees = [dev_member]
    db.add(task_payment)

    # Task 2: Blocked Critical Task
    task_k8s = Task(
        project_id=project.id,
        title="Setup Production Kubernetes Cluster & Ingress",
        description="Provision AWS EKS cluster, set up Cert-Manager and Nginx Ingress.",
        status_id=statuses["Blocked"].id,
        type_id=types["Task"].id,
        priority_id=priorities["Critical"].id,
        assigner_id=lead_member.id,
        estimated_hours=16.0,
        actual_hours=4.0,
        due_date=now + timedelta(days=2),
    )
    task_k8s.assignees = [dev_member]
    db.add(task_k8s)

    # Task 3: In-Progress database optimization (parallel workload)
    task_db = Task(
        project_id=project.id,
        title="Optimize ERP Slow Database Queries",
        description="Add indexes and optimize raw queries in inventory module.",
        status_id=statuses["In Progress"].id,
        type_id=types["Task"].id,
        priority_id=priorities["Medium"].id,
        assigner_id=lead_member.id,
        estimated_hours=8.0,
        actual_hours=2.0,
        due_date=now + timedelta(days=3),
    )
    task_db.assignees = [dev_member]
    db.add(task_db)

    # Task 4: In-Progress Auth Refactoring (parallel workload)
    task_auth = Task(
        project_id=project.id,
        title="Refactor OAuth Middleware & Token Caching",
        description="Refactor custom JWT token caching inside Redis store.",
        status_id=statuses["In Progress"].id,
        type_id=types["Task"].id,
        priority_id=priorities["High"].id,
        assigner_id=lead_member.id,
        estimated_hours=12.0,
        actual_hours=1.0,
        due_date=now + timedelta(days=4),
    )
    task_auth.assignees = [dev_member]
    db.add(task_auth)

    # Task 5: [Test Phase 2] Missing Estimate Task (triggers High Urgency Data Gap)
    task_missing_est = Task(
        project_id=project.id,
        title="[Test Phase 2] Stripe API Webhook Security Verification",
        description="Verify security signatures on incoming Stripe webhook events.",
        status_id=statuses["In Progress"].id,
        type_id=types["Task"].id,
        priority_id=priorities["High"].id,
        assigner_id=lead_member.id,
        estimated_hours=None,  # No estimate!
        actual_hours=0.0,
        due_date=now + timedelta(days=2),
    )
    task_missing_est.assignees = [dev_member]
    db.add(task_missing_est)

    # Task 6: [Test Phase 2] Stale Task & Missing Checkpoint (triggers Stale Task Outreach)
    task_stale_chk = Task(
        project_id=project.id,
        title="[Test Phase 2] Docker Compose Local Cache Tuning",
        description="Tune file sync caches inside docker-compose setup to optimize rebuilds.",
        status_id=statuses["In Progress"].id,
        type_id=types["Task"].id,
        priority_id=priorities["Medium"].id,
        assigner_id=lead_member.id,
        estimated_hours=8.0,
        actual_hours=1.0,
        start_date=now - timedelta(days=2),  # started 2 days ago, no checkpoint!
        due_date=now + timedelta(days=2),
        updated_at=now - timedelta(hours=26),  # stale!
    )
    task_stale_chk.assignees = [dev_member]
    db.add(task_stale_chk)

    db.flush()

    # 10. Create Task Checkpoints to trigger AI Risk Signals
    checkpoint_payment = TaskCheckpoint(
        task_id=task_payment.id,
        reported_by=mock_dev.id,
        progress_pct=40,
        remaining_hours=12.0,  # Estimated (20) < actual (28) + remaining (12)
        is_blocked=False,
    )
    db.add(checkpoint_payment)

    checkpoint_k8s = TaskCheckpoint(
        task_id=task_k8s.id,
        reported_by=mock_dev.id,
        progress_pct=10,
        remaining_hours=14.0,
        is_blocked=True,
        blocked_reason="AWS cloud resource quota exceeded. Pending enterprise account approval.",
    )
    db.add(checkpoint_k8s)

    db.commit()

    return ResponseSchema(
        data={
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
                {
                    "id": task_db.id,
                    "title": task_db.title,
                },
                {
                    "id": task_auth.id,
                    "title": task_auth.title,
                },
                {
                    "id": task_missing_est.id,
                    "title": task_missing_est.title,
                },
                {
                    "id": task_stale_chk.id,
                    "title": task_stale_chk.title,
                },
            ],
        },
        message="Realistic enterprise project test dataset generated successfully!",
    )
