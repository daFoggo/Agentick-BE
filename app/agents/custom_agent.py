import json
from typing import Any, Dict, List, Optional

from opik import track

from app.core.config import configs
from app.schema.agent_schema import AgentMessage
from app.agents.llm_strategy import LLMStrategy, OpenRouterStrategy


class CustomAgent:
    def __init__(self, strategy: Optional[LLMStrategy] = None):
        # Initialize default strategy if none provided
        if strategy is None:
            strategy = OpenRouterStrategy(
                api_key=configs.OPENROUTER_API_KEY,
                base_url=configs.OPENROUTER_BASE_URL,
                model=configs.OPENROUTER_MODEL,
            )
        self.strategy = strategy

    @track(entrypoint=True, name="run_agent_loop", project_name="Agentick")
    async def run(
        self,
        project_id: str,
        prompt: str,
        history: List[AgentMessage],
        tools: List[Dict[str, Any]],
        tool_executor: str,
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

        tool_calls_executed = []

        # --- CALL 1 ---
        res_json = await self.strategy.generate_chat_completion(
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        message = res_json["choices"][0]["message"]

        prompt_tokens = res_json.get("usage", {}).get("prompt_tokens", 0)
        completion_tokens = res_json.get("usage", {}).get("completion_tokens", 0)
        total_tokens = res_json.get("usage", {}).get("total_tokens", 0)

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

            # --- CALL 2 ---
            final_res_json = await self.strategy.generate_chat_completion(
                messages=messages,
                tools=None,
            )

            final_content = final_res_json["choices"][0]["message"]["content"]

            prompt_tokens += final_res_json.get("usage", {}).get("prompt_tokens", 0)
            completion_tokens += final_res_json.get("usage", {}).get(
                "completion_tokens", 0
            )
            total_tokens += final_res_json.get("usage", {}).get("total_tokens", 0)
        else:
            final_content = message["content"]

        # Log token usage to Opik Span
        try:
            from opik import opik_context

            opik_context.update_current_span(
                usage={
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                }
            )
        except Exception as opik_err:
            print(f"Failed to update Opik span usage: {opik_err}")

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
        messages = [{"role": "user", "content": prompt}]
        res_json = await self.strategy.generate_chat_completion(messages=messages)

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

        return res_json["choices"][0]["message"]["content"]
