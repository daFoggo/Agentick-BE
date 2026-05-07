import json
from typing import Any, Dict, List

import httpx
from opik import track

from app.core.config import configs
from app.schema.agent_schema import AgentMessage


class CustomAgent:
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or configs.OPENROUTER_API_KEY
        self.base_url = base_url or configs.OPENROUTER_BASE_URL
        self.model = model or configs.OPENROUTER_MODEL

    @track(entrypoint=True, name="run_agent_loop", project_name="Agentick")
    async def run(
        self,
        project_id: str,
        prompt: str,
        history: List[AgentMessage],
        tools: List[Dict[str, Any]],
        tool_executor: Any,
    ) -> Dict[str, Any]:
        system_instruction = (
            "You are Agentick AI Assistant, a smart agent helping with project management. "
            f"You are working in Project ID: {project_id}. "
            "You can use tools to create, read, and update tasks on behalf of users. "
            "Always reply politely in English. "
            "If the user asks to do something that matches a tool, execute the tool first, "
            "then report the result to the user."
        )

        messages = [{"role": "system", "content": system_instruction}]
        for msg in history:
            messages.append(msg.model_dump(exclude_none=True))
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://agentick.ai",
            "X-OpenRouter-Title": "Agentick",
            "Content-Type": "application/json",
        }

        tool_calls_executed = []

        async with httpx.AsyncClient() as client:
            payload = {
                "model": self.model,
                "messages": messages,
                "tools": tools,
                "tool_choice": "auto",
            }

            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            res_json = response.json()
            message = res_json["choices"][0]["message"]

            if "tool_calls" in message and message["tool_calls"]:
                tool_calls = message["tool_calls"]
                messages.append(message)

                for tool_call in tool_calls:
                    func_name = tool_call["function"]["name"]
                    func_args = json.loads(tool_call["function"]["arguments"])
                    tool_calls_executed.append(func_name)

                    # execute tool via the executor
                    tool_result = await tool_executor(func_name, func_args)

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": func_name,
                            "content": json.dumps(tool_result),
                        }
                    )

                final_payload = {"model": self.model, "messages": messages}
                final_response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=final_payload,
                    headers=headers,
                    timeout=30.0,
                )
                final_response.raise_for_status()
                final_res_json = final_response.json()
                final_content = final_res_json["choices"][0]["message"]["content"]
            else:
                final_content = message["content"]

            return {
                "response": final_content,
                "tool_calls_executed": tool_calls_executed,
            }

    @track(name="compose_outreach_email", project_name="Agentick")
    async def compose_outreach_email(
        self,
        task_title: str,
        due_date: str,
        days_to_deadline: int,
        hours_stale: float,
        assignee_name: str,
        gaps: List[Dict[str, Any]],
    ) -> str:
        prompt = f"""
You are a friendly, professional AI project management assistant named Agentick.
Compose a short email (maximum 5 sentences) to {assignee_name} asking for missing information regarding their task.

Task Information:
- Name: {task_title}
- Deadline: {due_date} ({days_to_deadline} days away)
- Last update: {hours_stale:.0f} hours ago

Missing Information to request:
{json.dumps(gaps, ensure_ascii=False)}

Requirements:
- Written in polite, friendly, and professional English.
- Avoid generic placeholders or cliché phrases like "Dear", "Sincerely", "Best regards", or "I hope this email finds you well".
- Explain why this information is needed (e.g., to enable automated deadline prediction and risk detection).
- End with a friendly closing call-to-action to update directly.
"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://agentick.ai",
            "X-OpenRouter-Title": "Agentick",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient() as client:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
            }
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            res_json = response.json()
            return res_json["choices"][0]["message"]["content"]
