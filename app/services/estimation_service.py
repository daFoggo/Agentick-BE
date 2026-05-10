import json

import httpx
from opik import track
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.custom_agent import CustomAgent
from app.model.task import Task
from app.utils.qdrant_helper import search_similar_tasks


class EstimationService:
    def __init__(self, db: Session):
        self.db = db
        self.agent = CustomAgent()

    @track(name="estimate_task_deadline", project_name="Agentick")
    async def estimate_task(
        self, project_id: str, title: str, description: str
    ) -> dict:
        """
        Multi-step Deadline Estimation Workflow:
        1. Retrieve similar tasks from Qdrant.
        2. Load their DB details (estimated vs actual).
        3. Analyze historical error variance.
        4. LLM-based reasoning & final estimation.
        """
        # Step 1: Retrieve similar tasks via semantic search
        query_text = f"{title} {description or ''}"
        similar_points = await search_similar_tasks(project_id, query_text, limit=5)

        # Step 2: Load DB details for these tasks
        historical_cases = []
        if similar_points:
            task_ids = [pt["task_id"] for pt in similar_points]
            tasks = self.db.scalars(select(Task).where(Task.id.in_(task_ids))).all()

            for t in tasks:
                historical_cases.append(
                    {
                        "title": t.title,
                        "description": t.description or "",
                        "estimated_hours": t.estimated_hours,
                        "actual_hours": t.actual_hours,
                        "variance": t.actual_hours - (t.estimated_hours or 0.0),
                    }
                )

        # Step 3: Compile context and run multi-step reasoning LLM call
        prompt = f"""
You are the Agentick AI Estimator, specializing in precise task duration estimation using Case-Based Reasoning (CBR).
Analyze the new task and the similar completed tasks from the past to estimate the optimal `estimated_hours`.

New Task:
- Title: "{title}"
- Description: "{description or "No description"}"

Similar Historical Tasks (Completed):
{json.dumps(historical_cases, indent=2)}

Output your response as a valid JSON object containing exactly:
- "suggested_hours": A float representing the suggested estimated hours.
- "rationale": A brief description of your reasoning (strictly max 15 words).
- "similar_cases_count": {len(historical_cases)}
- "reasoning_steps": {{
    "similarity_analysis": "Brief similarity analysis (strictly max 15 words)",
    "variance_analysis": "Brief variance analysis (strictly max 15 words)"
  }}

CRITICAL: Keep all text values extremely brief and under 15 words. Do not include markdown blocks or any text outside of the JSON.
"""
        headers = {
            "Authorization": f"Bearer {self.agent.api_key}",
            "HTTP-Referer": "https://agentick.ai",
            "X-OpenRouter-Title": "Agentick",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": self.agent.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,
                    "max_tokens": 300,
                }
                response = await client.post(
                    f"{self.agent.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )
                response.raise_for_status()
                res_json = response.json()

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

                content = res_json["choices"][0]["message"]["content"].strip()

                # Strip markdown blocks if present
                import re

                match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
                if match:
                    content = match.group(1)

                result = json.loads(content)
                return result
        except Exception as e:
            # Fallback estimation based on past cases average or defaults
            print(f"Estimation LLM call failed: {e}")
            if historical_cases:
                avg_actual = sum(c["actual_hours"] for c in historical_cases) / len(
                    historical_cases
                )
                suggested = avg_actual if avg_actual > 0 else 8.0
            else:
                suggested = 8.0

            return {
                "suggested_hours": suggested,
                "rationale": "Fallback calculation based on average actual hours of historical tasks.",
                "similar_cases_count": len(historical_cases),
                "reasoning_steps": {
                    "similarity_analysis": "Completed via programmatic fallback.",
                    "variance_analysis": "Completed via programmatic fallback.",
                },
            }
