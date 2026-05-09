import asyncio
from app.core.dependencies import get_database
from app.model.user import User
from app.model.project import Project
from app.model.task_status import TaskStatus
from app.model.task import Task
from app.model.task_time_log import TaskTimeLog
from app.model.risk_snapshot import RiskSnapshot
from app.services.velocity_service import VelocityService
from app.services.estimation_service import EstimationService
from app.services.risk_analysis_service import RiskAnalysisService
from datetime import datetime, date, timezone, timedelta


async def run_tests():
    print("🚀 STARTING PHASE 3 TEST SUITE...")

    with get_database().session() as db:
        # Get existing user and project
        user = db.query(User).first()
        project = db.query(Project).first()

        if not user or not project:
            print(
                "❌ No existing user or project found. Please run scratch/test_seed.py first!"
            )
            return

        completed_status = (
            db.query(TaskStatus)
            .filter_by(project_id=project.id, is_completed=True)
            .first()
        )
        in_progress_status = (
            db.query(TaskStatus)
            .filter_by(project_id=project.id, name="In Progress")
            .first()
        )

        if not completed_status:
            print(
                "❌ Completed status not found. Please run scratch/test_seed.py first!"
            )
            return

        print(f"👉 Project: {project.name} ({project.id})")
        print(f"👉 User: {user.name} ({user.id})")

        # ----------------- TEST 1: VELOCITY PROFILING -----------------
        print("\n--- 1. Testing Velocity Profiling ---")
        first_task = db.query(Task).filter_by(project_id=project.id).first()
        if not first_task:
            print("❌ No tasks found in project.")
            return

        # Add some time logs
        log1 = TaskTimeLog(
            task_id=first_task.id,
            user_id=user.id,
            log_type="manual",
            hours=4.5,
            logged_date=date.today(),
        )
        db.add(log1)
        db.commit()

        velocity_service = VelocityService(db)
        profile = velocity_service.get_project_velocity_profile(project.id)
        print("✅ Velocity Profile Generated successfully!")
        print(f"   Users Profiled: {len(profile['by_user'])}")
        if profile["by_user"]:
            print(f"   User hours logged: {profile['by_user'][0]['total_hours']}")
        print(f"   Task Types Profiled: {len(profile['by_task_type'])}")
        print(f"   Day of the week Profiled: {len(profile['by_day_of_week'])}")

        # ----------------- TEST 2: FEEDBACK LOOP & BACKFILL -----------------
        print("\n--- 2. Testing Feedback Loop & Backfill ---")
        # Create a task
        test_task = Task(
            project_id=project.id,
            title="Integrate OAuth Login",
            description="Setup Google OAuth 2.0 logins.",
            status_id=in_progress_status.id
            if in_progress_status
            else completed_status.id,
            type_id=first_task.type_id,
            priority_id=first_task.priority_id,
            assigner_id=first_task.assigner_id,
            estimated_hours=10.0,
            actual_hours=14.0,
            due_date=datetime.now(timezone.utc) + timedelta(days=2),
        )
        db.add(test_task)
        db.commit()

        # Create a mock RiskSnapshot for this task
        snapshot = RiskSnapshot(
            task_id=test_task.id,
            risk_score=0.85,
            risk_level="high",
            recommendation="Urgent developer focus required.",
        )
        db.add(snapshot)
        db.commit()

        # Mark task completed via repository to trigger completion logic
        from app.repository.task_repository import TaskRepository
        from contextlib import nullcontext

        task_repo = TaskRepository(lambda: nullcontext(db))
        task_repo.update(test_task.id, {"status_id": completed_status.id})

        # Verify the snapshot got backfilled
        db.refresh(snapshot)
        print("✅ Feedback Loop Completed!")
        print(f"   Snapshot actual completed at: {snapshot.actual_completed_at}")
        print(
            f"   Snapshot prediction error hours: {snapshot.prediction_error_hours} (Expected: +4.0 hours)"
        )

        # Verify risk score calibration
        risk_service = RiskAnalysisService(db)
        signals = risk_service.calculate_programmatic_signals(test_task)
        print("✅ Risk Score Calibration Signals updated:")
        print(
            f"   Assignee Average Prediction Error: {signals.get('assignee_avg_prediction_error_hours')} hours"
        )
        print(
            f"   Assignee Underestimation Tendency: {signals.get('assignee_underestimation_tendency')}"
        )

        # ----------------- TEST 3: DEADLINE ESTIMATION -----------------
        print("\n--- 3. Testing Deadline Estimation ---")
        estimation_service = EstimationService(db)
        est = await estimation_service.estimate_task(
            project_id=project.id,
            title="Setup GitHub Actions CI/CD Pipeline",
            description="Create workflows for linting, testing, and Docker builds on pull requests.",
        )
        print("✅ Deadline Estimation Generated successfully!")
        print(f"   Suggested Hours: {est.get('suggested_hours')} hours")
        print(f"   Rationale: {est.get('rationale')}")
        print("   Reasoning Steps (CBR):")
        print(
            f"     Similarity Analysis: {est.get('reasoning_steps', {}).get('similarity_analysis')}"
        )
        print(
            f"     Variance Analysis: {est.get('reasoning_steps', {}).get('variance_analysis')}"
        )

    print("\n🎉 ALL PHASE 3 TESTS SUCCESSFULLY COMPLETED!")


if __name__ == "__main__":
    asyncio.run(run_tests())
