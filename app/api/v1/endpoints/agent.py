from fastapi import APIRouter, BackgroundTasks, Depends

from app.api.v1.endpoints.project_tasks import get_task_service
from app.api.v1.endpoints.projects import get_project_permission_service
from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import AuthError, NotFoundError
from app.model.user import User
from app.schema.base_schema import ResponseSchema
from app.services.risk_analysis_service import RiskAnalysisService
from app.services.task_service import TaskService
from app.services.testing_service import TestingService
from app.services.project_permission_service import ProjectPermissionService

router = APIRouter(prefix="/agent", tags=["agent"])


def get_risk_analysis_service(db=Depends(get_db)) -> RiskAnalysisService:
    return RiskAnalysisService(db=db)


@router.post("/tasks/{task_id}/risk-analyses", response_model=ResponseSchema)
async def analyze_task_risk(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RiskAnalysisService = Depends(get_risk_analysis_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    permission_service.ensure_task_write(task_id, current_user.id)
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
    if not current_user.is_superuser:
        raise AuthError(detail="Only superusers can trigger global outreach.")

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
    task_service: TaskService = Depends(get_task_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    """
    Trigger risk analysis for all active tasks in a project in parallel.
    Uses separate concurrency-safe DB sessions for each task to avoid transaction conflicts.
    """
    import asyncio

    from app.core.dependencies import get_database

    permission_service.ensure_project_manage(project_id, current_user.id)
    active_task_ids = task_service._repository.get_active_task_ids_by_project(
        project_id
    )

    if not active_task_ids:
        return ResponseSchema(
            data={"analyzed_count": 0}, message="No active tasks to analyze"
        )

    async def analyze_single_task_safely(task_id: str):
        try:
            with get_database().session() as session:
                task_service_instance = RiskAnalysisService(db=session)
                await task_service_instance.analyze_task(task_id=task_id)
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
    """
    Special debug endpoint to generate realistic enterprise test datasets.
    Uses TestingService backend to insulate controller logic.
    """
    if user_id and user_id != current_user.id and not current_user.is_superuser:
        raise AuthError(
            detail="Only superusers can generate test data for another user."
        )

    if user_id and db.get(User, user_id) is None:
        raise NotFoundError(detail=f"User with ID {user_id} not found.")

    data = TestingService.generate_mock_project_data(
        db=db,
        current_user=current_user,
        user_id=user_id,
        project_name=project_name,
        timezone=timezone,
    )
    return ResponseSchema(
        data=data,
        message="Realistic enterprise project test dataset generated successfully!",
    )


@router.post("/morning-scan/trigger", response_model=ResponseSchema)
async def trigger_morning_scan_manually(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
):
    """
    Emergency trigger for demo purposes. Forces morning risk scan immediately on ALL tasks
    without waiting for project's local 9:00 AM.
    """
    if not current_user.is_superuser:
        raise AuthError(detail="Only superusers can trigger global morning scans.")

    from app.core.dependencies import get_database
    from app.services.testing_service import TestingService

    async def run_scan():
        with get_database().session() as db:
            await TestingService.trigger_morning_scan_now(db)

    background_tasks.add_task(run_scan)
    return ResponseSchema(
        data={"status": "queued"},
        message="Forced morning risk scan queued successfully.",
    )


@router.post("/evening-summary/trigger", response_model=ResponseSchema)
async def trigger_evening_summary_manually(
    background_tasks: BackgroundTasks,
    project_id: str | None = None,
    current_user: User = Depends(get_current_active_user),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    """
    Emergency trigger for demo purposes. Forces the dispatch of the Daily Risk Summary Email report immediately
    to the project team lead without waiting for the scheduled cycle.
    """
    if project_id:
        permission_service.ensure_project_manage(project_id, current_user.id)
    elif not current_user.is_superuser:
        raise AuthError(detail="Only superusers can trigger global summaries.")

    from app.core.dependencies import get_database
    from app.services.testing_service import TestingService

    async def run_summary():
        with get_database().session() as db:
            await TestingService.trigger_evening_summary_now(db, project_id)

    background_tasks.add_task(run_summary)
    return ResponseSchema(
        data={"status": "queued"},
        message="Forced evening summary report generation queued successfully.",
    )
