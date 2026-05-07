from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.model.task import Task
from app.model.user import User
from app.model.risk_snapshot import RiskSnapshot
from app.model.agent_outreach import AgentOutreach
from app.model.task_checkpoint import TaskCheckpoint
from app.model.task_time_log import TaskTimeLog
from app.agents.custom_agent import CustomAgent
from app.utils.email import send_agent_outreach_email


class AgentOutreachService:
    def __init__(self, db: Session):
        self.db = db
        self.agent = CustomAgent()

    def assess_data_gap(self, task: Task) -> Dict[str, Any]:
        """
        Determines what data gaps exist for a task.
        """
        gaps = []
        urgency = "low"

        # 1. Critical Gap: Estimated Hours missing
        if task.estimated_hours is None:
            gaps.append({
                "field": "estimated_hours",
                "question": "How many hours do you estimate this task will take to complete?",
                "urgency": "high"
            })
            urgency = "high"

        # 2. Important Gap: Task is active but has no progress checkpoints logged after start date
        if task.start_date:
            now_utc = datetime.now(timezone.utc)
            days_since_start = (now_utc - task.start_date).days
            
            # Check if there are checkpoints
            checkpoints_exist = self.db.scalar(
                select(TaskCheckpoint)
                .where(TaskCheckpoint.task_id == task.id)
                .limit(1)
            ) is not None
            
            if days_since_start > 1 and not checkpoints_exist:
                gaps.append({
                    "field": "progress",
                    "question": "What is the current progress level and how many remaining hours do you expect?",
                    "urgency": "medium"
                })
                if urgency != "high":
                    urgency = "medium"

        return {"gaps": gaps, "urgency": urgency}

    def should_send_stale_alert(self, task: Task) -> bool:
        """
        Checks anti-spam filters before allowing a stale update notification.
        """
        # Do not send if task is in todo/done/completed/archived
        status_name = task.status.name.lower() if task.status else ""
        if status_name in ["todo", "done", "completed", "archived"]:
            return False

        now_utc = datetime.now(timezone.utc)

        # Do not send if no due_date or start_date
        if not task.due_date or not task.start_date:
            return False

        days_to_deadline = (task.due_date - now_utc).days
        days_since_start = (now_utc - task.start_date).days

        # Do not send if deadline is far and task just started
        if days_to_deadline > 3 and days_since_start < 2:
            return False

        # Do not send if the deadline is too far away (> 3 days)
        if days_to_deadline > 3:
            return False

        # Do not send if already sent an alert of this type in the last 24 hours
        last_outreach = self.db.scalars(
            select(AgentOutreach)
            .where(AgentOutreach.task_id == task.id)
            .order_by(desc(AgentOutreach.sent_at))
            .limit(1)
        ).first()

        if last_outreach:
            hours_since_alert = (now_utc - last_outreach.sent_at).total_seconds() / 3600
            if hours_since_alert < 24:
                return False

        # Get last activity
        last_time_log = self.db.scalars(
            select(TaskTimeLog)
            .where(TaskTimeLog.task_id == task.id)
            .order_by(desc(TaskTimeLog.created_at))
            .limit(1)
        ).first()

        last_checkpoint = self.db.scalars(
            select(TaskCheckpoint)
            .where(TaskCheckpoint.task_id == task.id)
            .order_by(desc(TaskCheckpoint.created_at))
            .limit(1)
        ).first()

        last_activity = max(
            task.updated_at,
            last_time_log.created_at if last_time_log else task.updated_at,
            last_checkpoint.created_at if last_checkpoint else task.updated_at
        )

        hours_stale = (now_utc - last_activity).total_seconds() / 3600

        # Do not send if updated within the last 2 hours (user is active)
        if hours_stale < 2.0:
            return False

        # Send if stale for > 24 hours AND deadline is close (<= 3 days)
        return hours_stale > 24.0 and days_to_deadline <= 3

    async def run_outreach_cycle(self) -> List[Dict[str, Any]]:
        """
        Runs the full check for all active tasks, composes context-aware emails using LLM and sends them.
        """
        # Fetch active tasks
        tasks = self.db.scalars(
            select(Task)
            .where(Task.is_archived == False)
            .where(Task.is_deleted == False)
        ).all()

        outreaches_sent = []
        now_utc = datetime.now(timezone.utc)

        for task in tasks:
            status_name = task.status.name.lower() if task.status else ""
            if status_name in ["done", "completed", "todo"]:
                continue

            # Skip if there are no assignees assigned to this task
            if not task.assignees:
                continue

            # Check gaps and stale status
            gap_report = self.assess_data_gap(task)
            stale_alert = self.should_send_stale_alert(task)

            should_outreach = False
            outreach_type = None
            gaps_to_report = []

            if gap_report["urgency"] == "high":
                should_outreach = True
                outreach_type = "missing_estimate"
                gaps_to_report = gap_report["gaps"]
            elif stale_alert:
                should_outreach = True
                outreach_type = "stale_update"
                gaps_to_report = gap_report["gaps"] if gap_report["gaps"] else [
                    {
                        "field": "general_update",
                        "question": "Can you please provide a general progress update or checkpoint for this task?",
                        "urgency": "medium"
                    }
                ]

            if should_outreach and outreach_type:
                days_to_deadline = (task.due_date - now_utc).days if task.due_date else 0
                hours_stale = (now_utc - task.updated_at).total_seconds() / 3600

                for assignee in task.assignees:
                    user_obj = assignee.user
                    if not user_obj or not user_obj.email:
                        continue

                    # Compose email via LLM CustomAgent
                    email_body = await self.agent.compose_outreach_email(
                        task_title=task.title,
                        due_date=str(task.due_date),
                        days_to_deadline=days_to_deadline,
                        hours_stale=hours_stale,
                        assignee_name=user_obj.name,
                        gaps=gaps_to_report,
                    )

                    subject = f"Action Required: Update for '{task.title}'"
                    task_link = f"https://agentick.app/tasks/{task.id}"

                    # Send email
                    send_agent_outreach_email(
                        email_to=user_obj.email,
                        subject=subject,
                        body_content=email_body,
                        task_link=task_link,
                    )

                    # Log outreach record
                    outreach_log = AgentOutreach(
                        task_id=task.id,
                        user_id=user_obj.id,
                        outreach_type=outreach_type,
                        channel="email",
                        sent_at=now_utc,
                    )
                    self.db.add(outreach_log)

                    # Create or update RiskSnapshot for memory
                    snapshot = RiskSnapshot(
                        task_id=task.id,
                        risk_score=0.8 if outreach_type == "missing_estimate" else 0.6,
                        risk_level="high" if outreach_type == "missing_estimate" else "medium",
                        alert_type="data_gap" if outreach_type == "missing_estimate" else "stale",
                        alert_sent=True,
                        alert_sent_at=now_utc,
                        signals=[f"Outreach sent due to: {outreach_type}"],
                        recommendation="Prompt user to input accurate estimations & checkpoints.",
                    )
                    self.db.add(snapshot)

                    outreaches_sent.append({
                        "task_id": task.id,
                        "user_id": user_obj.id,
                        "outreach_type": outreach_type,
                        "email": user_obj.email,
                        "email_body": email_body,
                    })

        if outreaches_sent:
            self.db.commit()

        return outreaches_sent
