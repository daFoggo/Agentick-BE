from app.core.dependencies import get_database
from app.model.user import User
from app.model.team import Team
from app.model.project import Project
from app.model.project_member import ProjectMember
from app.model.task_status import TaskStatus
from app.model.task_priority import TaskPriority
from app.model.task_type import TaskType
from app.model.work_schedule import WorkSchedule
from app.model.task import Task
from app.model.task_checkpoint import TaskCheckpoint
from app.model.task_member import TaskMember
from datetime import datetime, timedelta
import pytz
from app.core.security import get_password_hash

print("Starting seed test...")

with get_database().session() as db:
    user = db.query(User).first()
    if not user:
        user = User(
            email="test_lead@agentick.com",
            name="Test Lead",
            hashed_password=get_password_hash("password123"),
            user_token="test_lead_token",
            is_active=True,
        )
        db.add(user)
        db.flush()

    print(f"Using user: {user.name} ({user.id})")

    # 1. Create Mock Team owned by Target User
    team = Team(
        name=f"Enterprise Cloud Dev Team ({user.name})",
        description="Realistic mock team for AI Agent testing",
        owner_id=user.id,
    )
    db.add(team)
    db.flush()

    # 2. Create Mock Project inside the Team
    project = Project(
        team_id=team.id,
        name="Enterprise ERP Core Platform",
        description="Corporate ERP system migration to cloud",
        timezone="Asia/Ho_Chi_Minh",
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
    lead_member = ProjectMember(project_id=project.id, user_id=user.id, role="manager")
    db.add(lead_member)
    db.flush()

    # 7. Create/Find Mock Developer and Tester Users
    mock_dev_email = f"dev_{team.id[:8]}@agentick.com"
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
    mock_tester = User(
        email=mock_tester_email,
        name="Tran Thi Tester",
        hashed_password=get_password_hash("password123"),
        user_token=f"token_{team.id[:8]}_tester",
        is_active=True,
    )
    db.add(mock_tester)
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
    for u_id in [mock_dev.id, mock_tester.id]:
        for d in range(7):
            is_off = d in [5, 6]
            sched = WorkSchedule(
                team_id=team.id,
                user_id=u_id,
                day_of_week=d,
                start_time="09:00" if not is_off else None,
                end_time="18:00" if not is_off else None,
                is_off=is_off,
            )
            db.add(sched)
    db.flush()

    # 9. Create Tasks
    now = datetime.now(pytz.utc)
    task_payment = Task(
        project_id=project.id,
        title="Implement Stripe Payment Gateway Integration",
        description="Integrate Stripe Checkout.",
        status_id=statuses["In Progress"].id,
        type_id=types["Task"].id,
        priority_id=priorities["High"].id,
        estimated_hours=20.0,
        actual_hours=28.0,
        due_date=now + timedelta(days=1),
    )
    db.add(task_payment)
    db.flush()
    db.add(TaskMember(task_id=task_payment.id, user_id=user.id, role="lead"))
    db.add(TaskMember(task_id=task_payment.id, user_id=mock_dev.id, role="member"))

    task_k8s = Task(
        project_id=project.id,
        title="Setup Production Kubernetes Cluster",
        description="EKS cluster.",
        status_id=statuses["Blocked"].id,
        type_id=types["Task"].id,
        priority_id=priorities["Critical"].id,
        estimated_hours=16.0,
        actual_hours=4.0,
        due_date=now + timedelta(days=2),
    )
    db.add(task_k8s)
    db.flush()
    db.add(TaskMember(task_id=task_k8s.id, user_id=user.id, role="lead"))
    db.add(TaskMember(task_id=task_k8s.id, user_id=mock_dev.id, role="member"))
    db.flush()

    # 10. Checkpoints with reported_by
    checkpoint_payment = TaskCheckpoint(
        task_id=task_payment.id,
        reported_by=mock_dev.id,
        progress_pct=40,
        remaining_hours=12.0,
        is_blocked=False,
    )
    db.add(checkpoint_payment)

    checkpoint_k8s = TaskCheckpoint(
        task_id=task_k8s.id,
        reported_by=mock_dev.id,
        progress_pct=10,
        remaining_hours=14.0,
        is_blocked=True,
        blocked_reason="EKS quota.",
    )
    db.add(checkpoint_k8s)

    db.commit()
    print("SUCCESSFUL!")
