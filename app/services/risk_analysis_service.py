import json
import httpx
from datetime import datetime, timezone, timedelta
from typing import Any, Dict
from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session
from opik import track

from app.services.base_service import BaseService
from app.agents.custom_agent import CustomAgent
from app.model.task import Task
from app.model.task_checkpoint import TaskCheckpoint
from app.model.work_schedule import WorkSchedule
from app.model.risk_snapshot import RiskSnapshot
from app.model.project_member import ProjectMember
from app.utils.email import send_risk_alert_email
from app.core.config import configs


class RiskAnalysisService(BaseService):
    def __init__(self, db: Session, repository: Any = None):
        super().__init__(repository)
        self.db = db
        self.agent = CustomAgent()

    @track(name="calculate_programmatic_signals")
    def calculate_programmatic_signals(self, task: Task) -> Dict[str, Any]:
        """
        Calculates all risk metrics deterministically using Python code.
        """
        now_utc = datetime.now(timezone.utc)
        signals = {}

        # 1. Time Variance Factor
        estimated = task.estimated_hours or 0.0
        actual = task.actual_hours or 0.0
        variance = actual - estimated
        signals["estimated_hours"] = estimated
        signals["actual_hours"] = actual
        signals["time_variance_hours"] = variance
        signals["is_over_estimate"] = variance > 0 if estimated > 0 else False

        # 2. Checkpoint Factor
        last_checkpoint = self.db.scalars(
            select(TaskCheckpoint)
            .where(TaskCheckpoint.task_id == task.id)
            .order_by(desc(TaskCheckpoint.created_at))
            .limit(1)
        ).first()

        if last_checkpoint:
            signals["last_checkpoint_progress_pct"] = last_checkpoint.progress_pct
            signals["last_checkpoint_remaining_hours"] = last_checkpoint.remaining_hours
            signals["is_blocked"] = last_checkpoint.is_blocked
            signals["blocked_reason"] = last_checkpoint.blocked_reason
        else:
            signals["last_checkpoint_progress_pct"] = 0
            signals["last_checkpoint_remaining_hours"] = estimated
            signals["is_blocked"] = False
            signals["blocked_reason"] = None

        # 3. Schedule Factor (Working Hours Availability)
        assignees = task.assignees
        if assignees and task.due_date:
            primary_assignee = assignees[0]
            user_id = primary_assignee.user_id

            # Fetch work schedules
            schedules = self.db.scalars(
                select(WorkSchedule).where(WorkSchedule.user_id == user_id)
            ).all()

            # Map of day_of_week to working hours
            schedule_map = {s.day_of_week: s for s in schedules}

            # Calculate total working hours available until deadline
            total_working_hours_available = 0.0
            due_date = task.due_date

            temp_date = now_utc
            while temp_date <= due_date:
                day_num = temp_date.weekday()  # Monday is 0, Sunday is 6
                day_schedule = schedule_map.get(day_num)
                if day_schedule and not day_schedule.is_off:
                    if day_schedule.start_time and day_schedule.end_time:
                        try:
                            fmt = "%H:%M"
                            t1 = datetime.strptime(day_schedule.start_time, fmt)
                            t2 = datetime.strptime(day_schedule.end_time, fmt)
                            hrs = (t2 - t1).total_seconds() / 3600
                            total_working_hours_available += hrs
                        except Exception:
                            total_working_hours_available += 8.0
                    else:
                        total_working_hours_available += 8.0
                temp_date = temp_date + timedelta(days=1)

            remaining_needed = (
                last_checkpoint.remaining_hours
                if (last_checkpoint and last_checkpoint.remaining_hours is not None)
                else max(0.0, estimated - actual)
            )

            signals["available_working_hours"] = total_working_hours_available
            signals["remaining_needed_hours"] = remaining_needed
            signals["has_schedule_bottleneck"] = (
                remaining_needed > total_working_hours_available
            )
        else:
            signals["available_working_hours"] = None
            signals["remaining_needed_hours"] = max(0.0, estimated - actual)
            signals["has_schedule_bottleneck"] = False

        # 4. Congestion Factor (Parallel active tasks of assignee)
        if assignees:
            user_id = assignees[0].user_id
            # Subquery project members of this user
            member_ids = self.db.scalars(
                select(ProjectMember.id).where(ProjectMember.user_id == user_id)
            ).all()

            # Count parallel active (not Done / Completed) tasks
            parallel_tasks_count = self.db.scalar(
                select(func.count(Task.id))
                .join(Task.assignees)
                .where(ProjectMember.id.in_(member_ids))
                .where(Task.is_archived.is_(False))
                .where(Task.is_deleted.is_(False))
            )
            signals["parallel_tasks_count"] = parallel_tasks_count or 0
        else:
            signals["parallel_tasks_count"] = 0

        # 5. Feedback Loop Calibration (Error history)
        if assignees:
            user_id = assignees[0].user_id
            completed_snapshots = self.db.scalars(
                select(RiskSnapshot)
                .join(Task, Task.id == RiskSnapshot.task_id)
                .join(Task.assignees)
                .where(ProjectMember.user_id == user_id)
                .where(RiskSnapshot.prediction_error_hours.is_not(None))
            ).all()

            if completed_snapshots:
                errors = [s.prediction_error_hours for s in completed_snapshots]
                avg_error = sum(errors) / len(errors)
                signals["assignee_avg_prediction_error_hours"] = avg_error
                signals["assignee_underestimation_tendency"] = avg_error > 2.0
            else:
                signals["assignee_avg_prediction_error_hours"] = 0.0
                signals["assignee_underestimation_tendency"] = False
        else:
            signals["assignee_avg_prediction_error_hours"] = 0.0
            signals["assignee_underestimation_tendency"] = False

        return signals

    @track(name="run_task_risk_assessment", project_name="Agentick")
    async def analyze_task(self, task_id: str) -> RiskSnapshot:
        """
        Executes programmatic gate analysis, calls LLM to synthesize recommendation and saves RiskSnapshot.
        """
        task = self.db.get(Task, task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found.")

        # Calculate raw signals programmatically
        signals = self.calculate_programmatic_signals(task)

        # Call OpenRouter via CustomAgent to perform analysis
        prompt = f"""
You are the Agentick AI Project Manager (PM) Assistant. Analyze the following project task signals to determine a precise risk score and a high-level managerial recommendation for the Team Lead.

Task Meta:
- Title: "{task.title}"
- Description: "{task.description or "No description"}"
- Due Date: {task.due_date}

Calculated Risk Signals:
{json.dumps(signals, indent=2)}

Requirements:
- Output a single JSON object containing EXACTLY:
  1. "risk_score": A float between 0.0 (no risk) and 1.0 (critical danger of missing deadline).
  2. "risk_level": One of: "low", "medium", "high", "critical".
  3. "recommendation": A high-level managerial recommendation for the Team Lead in English.
     * Keep it extremely brief and concise (maximum 2 sentences, under 40 words).
     * Focus ONLY on managerial advice: reallocating resources, adjusting schedules, communicating with stakeholders, or unblocking team members.
     * DO NOT offer technical advice, code implementations, or specific technology recommendations (e.g., do NOT suggest Terraform, Helm, specific libraries, or dev-level task instructions).
- Do not output any additional conversational text or markdown code blocks other than the valid JSON object.
"""
        # Execute LLM call
        headers = {
            "Authorization": f"Bearer {self.agent.api_key}",
            "HTTP-Referer": "https://agentick.ai",
            "X-OpenRouter-Title": "Agentick",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            payload = {
                "model": self.agent.model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
            }
            response = await client.post(
                f"{self.agent.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            res_json = response.json()

            llm_output_text = None
            if "choices" in res_json and len(res_json["choices"]) > 0:
                llm_output_text = (
                    res_json["choices"][0].get("message", {}).get("content")
                )

            # Robust JSON extraction and parsing
            analysis_result = {}
            if llm_output_text:
                clean_text = llm_output_text.strip()
                import re

                # Strip markdown code blocks if present
                match = re.search(
                    r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL
                )
                if match:
                    clean_text = match.group(1)
                else:
                    start_idx = clean_text.find("{")
                    end_idx = clean_text.rfind("}")
                    if start_idx != -1 and end_idx != -1:
                        clean_text = clean_text[start_idx : end_idx + 1]

                try:
                    # strict=False permits control characters (like newlines) inside JSON values
                    analysis_result = json.loads(clean_text, strict=False)
                except Exception as parse_err:
                    print(
                        f"JSON Parse Error: {parse_err}. Raw LLM Output: {llm_output_text}"
                    )

            # Safe programmatic fallback if parsing fails or LLM output is empty
            if not analysis_result:
                has_bottleneck = signals.get("has_schedule_bottleneck", False)
                is_blocked = signals.get("is_blocked", False)

                if is_blocked:
                    risk_score = 0.95
                    risk_level = "critical"
                    recommendation = "The task is currently blocked. The Team Lead should immediately engage with stakeholders to resolve dependencies and unblock progress."
                elif has_bottleneck:
                    risk_score = 0.80
                    risk_level = "high"
                    recommendation = "A potential scheduling bottleneck has been detected. Consider reallocating available resources to ensure the task stays on track."
                else:
                    risk_score = 0.40
                    risk_level = "medium"
                    recommendation = "Monitor task progress daily to ensure that the remaining hours are logged correctly."

                analysis_result = {
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "recommendation": recommendation,
                }

            # Log token usage to Opik Span
            try:
                from opik import opik_context

                usage = res_json.get("usage", {})
                opik_context.update_current_span(
                    usage={
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    }
                )
            except Exception as opik_err:
                print(f"Failed to update Opik span usage: {opik_err}")

        risk_score = analysis_result.get("risk_score", 0.0)
        risk_level = analysis_result.get("risk_level", "low")
        recommendation = analysis_result.get("recommendation", "")

        # Save snapshot
        snapshot = RiskSnapshot(
            task_id=task.id,
            risk_score=risk_score,
            risk_level=risk_level,
            alert_type="high_risk" if risk_score >= 0.7 else None,
            signals=signals,
            recommendation=recommendation,
            predicted_completion_at=None,
        )
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)

        # Trigger proactive email alert if score >= 0.7
        if risk_score >= 0.7 and not snapshot.alert_sent:
            # Send alert to assignee(s)
            for pm in task.assignees:
                if pm.user and pm.user.email:
                    try:
                        due_str = (
                            task.due_date.strftime("%Y-%m-%d %H:%M")
                            if task.due_date
                            else "No deadline"
                        )
                        task_link = f"{configs.FRONTEND_URL}/tasks/{task.id}"
                        send_risk_alert_email(
                            email_to=pm.user.email,
                            task_title=task.title,
                            risk_score=risk_score,
                            risk_level=risk_level,
                            due_date=due_str,
                            recommendation=recommendation,
                            task_link=task_link,
                        )
                        snapshot.alert_sent = True
                        snapshot.alert_sent_at = datetime.now(timezone.utc)
                    except Exception as e:
                        print(f"Error sending email to {pm.user.email}: {e}")

            # Also send to the assigner
            if task.assigner and task.assigner.user and task.assigner.user.email:
                try:
                    due_str = (
                        task.due_date.strftime("%Y-%m-%d %H:%M")
                        if task.due_date
                        else "No deadline"
                    )
                    task_link = f"{configs.FRONTEND_URL}/tasks/{task.id}"
                    send_risk_alert_email(
                        email_to=task.assigner.user.email,
                        task_title=task.title,
                        risk_score=risk_score,
                        risk_level=risk_level,
                        due_date=due_str,
                        recommendation=recommendation,
                        task_link=task_link,
                    )
                except Exception as e:
                    print(f"Error sending email to assigner: {e}")

            # Commit the update for alert_sent status
            self.db.commit()

        return snapshot
