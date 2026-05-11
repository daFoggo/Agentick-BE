import asyncio
import os
import smtplib
from datetime import date, datetime
from datetime import timezone as pytimezone
from email.message import EmailMessage

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
from sqlalchemy import func, select, or_
from sqlalchemy.orm import joinedload

from app.core.config import configs
from app.core.dependencies import get_database
from app.model.project import Project
from app.model.risk_snapshot import RiskSnapshot
from app.model.task import Task
from app.model.task_status import TaskStatus
from app.services.risk_analysis_service import RiskAnalysisService
from datetime import timedelta

# Run the scheduler consistently on UTC, using dynamic offsets per job
scheduler = AsyncIOScheduler(timezone=timezone("UTC"))


async def morning_scan_job():
    """
    Morning scan: Runs hourly. For each active task, it checks if the current
    time in that task's project localized timezone is exactly 9:00 AM.
    If so, it runs the risk analysis.
    """
    with get_database().session() as db:
        now_utc = datetime.now(pytimezone.utc)
        # Stale cutoff: Don't analyze tasks overdue by more than 7 days (assumed abandoned)
        stale_cutoff = now_utc - timedelta(days=7)

        # SMART OPTIMIZATION: Push task filtering to DB level to avoid memory overhead
        # Only select tasks that are NOT completed, NOT archived, NOT deleted, and NOT extremely overdue.
        tasks = db.scalars(
            select(Task)
            .join(TaskStatus, TaskStatus.id == Task.status_id)
            .options(joinedload(Task.project))
            .where(Task.is_archived.is_(False))
            .where(Task.is_deleted.is_(False))
            .where(TaskStatus.is_completed.is_(False))
            .where(or_(Task.due_date.is_(None), Task.due_date >= stale_cutoff))
        ).all()

        db_factory = get_database()

        sem = asyncio.Semaphore(5)  # Prevent overwhelming API Rate Limits

        async def process_task(t_obj):
            # Early safety validation if task lost linkage
            if not t_obj.project:
                return

            proj_tz_name = (
                t_obj.project.timezone
                if (t_obj.project and t_obj.project.timezone)
                else "Asia/Ho_Chi_Minh"
            )
            try:
                proj_tz = timezone(proj_tz_name)
                localized_now = now_utc.astimezone(proj_tz)
            except Exception:
                proj_tz = timezone("Asia/Ho_Chi_Minh")
                localized_now = now_utc.astimezone(proj_tz)

            # Check if it's 9 AM in the project timezone
            if localized_now.hour == 9:
                async with sem:
                    # Create a completely separate and fresh session for thread-safety in async concurrency
                    with db_factory.session() as local_db:
                        try:
                            local_analyzer = RiskAnalysisService(local_db)
                            await local_analyzer.analyze_task(t_obj.id)
                        except Exception as ex:
                            print(f"Error analyzing task {t_obj.id}: {ex}")

        # Fire off all analysis processes concurrently
        await asyncio.gather(*[process_task(task) for task in tasks])


async def evening_summary_job():
    """
    Evening summary: Runs hourly. Checks projects to see if the current time
    in their localized timezone is 5:30 PM (hour == 17, minute >= 30, or simply hour == 17).
    If so, it aggregates today's snapshots for that project and emails the summary report to the Team Lead.
    """
    with get_database().session() as db:
        now_utc = datetime.now(pytimezone.utc)
        today = date.today()

        # Fetch all active projects
        projects = db.scalars(
            select(Project).where(Project.is_deleted.is_(False))
        ).all()

        for project in projects:
            proj_tz_name = project.timezone or "Asia/Ho_Chi_Minh"
            try:
                proj_tz = timezone(proj_tz_name)
                localized_now = now_utc.astimezone(proj_tz)
            except Exception:
                proj_tz = timezone("Asia/Ho_Chi_Minh")
                localized_now = now_utc.astimezone(proj_tz)

            # Trigger at 5:30 PM local project time (hour == 17)
            if localized_now.hour == 17:
                # Find snapshots generated today with risk score >= 0.5 for tasks in this project
                snapshots = db.scalars(
                    select(RiskSnapshot)
                    .join(Task, Task.id == RiskSnapshot.task_id)
                    .join(TaskStatus, TaskStatus.id == Task.status_id)
                    .where(Task.project_id == project.id)
                    .where(
                        TaskStatus.is_completed.is_(False)
                    )  # 🚀 SMART: Exclude resolved risks
                    .where(func.date(RiskSnapshot.created_at) == today)
                    .where(RiskSnapshot.risk_score >= 0.5)
                    .order_by(RiskSnapshot.risk_score.desc())
                ).all()

                if not snapshots:
                    continue

                team_lead_email = os.getenv("TEAM_LEAD_EMAIL") or configs.SMTP_USER
                if not team_lead_email:
                    print(f"No recipient email configured for project {project.name}.")
                    continue

                report_title = f"📋 [Agentick] Evening Summary - {project.name} - {today.strftime('%Y-%m-%d')}"

                html_content = f"""
                <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 650px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                            <h2 style="color: #2563eb; margin-top: 0;">📋 Project Daily Risk Summary</h2>
                            <p>Hello Team Lead,</p>
                            <p>Here is the tóm tắt báo cáo rủi ro công việc của dự án <b>{project.name}</b> trong ngày hôm nay <b>{today.strftime("%Y-%m-%d")}</b> (múi giờ: {proj_tz_name}):</p>
                            
                            <div style="margin: 20px 0;">
                """

                for idx, snap in enumerate(snapshots):
                    task = snap.task
                    assignee_name = "Unassigned"
                    members = task.task_members
                    if members:
                        target = next(
                            (m for m in members if m.role == "lead"), members[0]
                        )
                        if target and target.user:
                            assignee_name = target.user.name

                    color = "#e11d48" if snap.risk_score >= 0.7 else "#d97706"

                    html_content += f"""
                                <div style="border: 1px solid #e5e7eb; border-left: 5px solid {color}; padding: 15px; margin-bottom: 15px; border-radius: 4px; background-color: #f9fafb;">
                                    <h4 style="margin: 0 0 8px 0; color: #111827;">{idx + 1}. Task: {task.title}</h4>
                                    <p style="margin: 0 0 6px 0; font-size: 0.95em;"><b>Assignee:</b> {assignee_name}</p>
                                    <p style="margin: 0 0 6px 0; font-size: 0.95em;"><b>Risk Score:</b> <code style="color: {color}; font-weight: bold;">{snap.risk_score:.2f}</code> ({snap.risk_level.upper()})</p>
                                    <p style="margin: 0; font-size: 0.95em;"><b>Recommendation:</b> {snap.recommendation}</p>
                                </div>
                    """

                html_content += f"""
                            </div>
                            <p>Click the button below to view the manager dashboard:</p>
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{configs.FRONTEND_URL}/dashboard" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
                                    View Dashboard
                                </a>
                            </div>
                            <p>Thanks,<br>The {configs.EMAILS_FROM_NAME} Team</p>
                        </div>
                    </body>
                </html>
                """

                msg = EmailMessage()
                msg["Subject"] = report_title
                msg["From"] = f"{configs.EMAILS_FROM_NAME} <{configs.SMTP_USER}>"
                msg["To"] = team_lead_email
                msg.set_content(
                    f"Daily Risk Summary Report for {project.name} - {today.strftime('%Y-%m-%d')}\n\nPlease check the HTML version."
                )
                msg.add_alternative(html_content, subtype="html")

                if configs.SMTP_USER and configs.SMTP_PASSWORD:
                    try:
                        server = smtplib.SMTP(configs.SMTP_HOST, configs.SMTP_PORT)
                        server.starttls()
                        server.login(configs.SMTP_USER, configs.SMTP_PASSWORD)
                        server.send_message(msg)
                        server.quit()
                        print(
                            f"Successfully emailed daily summary report to {team_lead_email} for project {project.name}"
                        )
                    except Exception as e:
                        print(
                            f"Failed to send daily summary email for project {project.name}: {e}"
                        )
                else:
                    print(
                        f"[Mock Email] Evening Summary Report generated for {project.name} and sent to {team_lead_email}."
                    )


def start_scheduler():
    """
    Starts the APScheduler background runner.
    """
    # Run hourly at minute 0 (checks if it's currently 9:00 AM local time for each project)
    scheduler.add_job(morning_scan_job, "cron", minute=0, id="morning_scan")

    # Run hourly at minute 30 (checks if it's currently 5:30 PM/5:00 PM local time for each project)
    scheduler.add_job(evening_summary_job, "cron", minute=30, id="evening_summary")

    scheduler.start()


def shutdown_scheduler():
    """
    Gracefully shuts down the background scheduler.
    """
    scheduler.shutdown()
