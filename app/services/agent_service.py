import json
from typing import Any, Dict, List

import httpx
from opik import track

from app.core.config import configs
from app.schema.agent_schema import AgentMessage
from app.schema.task_schema import TaskCreate, TaskUpdate
from app.services.task_service import TaskService


class AgentService:
    def __init__(self, task_service: TaskService):
        self.task_service = task_service
        self.api_key = configs.OPENROUTER_API_KEY
        self.base_url = configs.OPENROUTER_BASE_URL
        self.model = configs.OPENROUTER_MODEL

        # Register tools
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "create_task",
                    "description": "Create a new task in the project.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "The ID of the project.",
                            },
                            "title": {
                                "type": "string",
                                "description": "The title of the task.",
                            },
                            "description": {
                                "type": "string",
                                "description": "Details about the task.",
                            },
                            "status_id": {
                                "type": "string",
                                "description": "The ID of the task status.",
                            },
                            "priority_id": {
                                "type": "string",
                                "description": "The ID of the task priority.",
                            },
                            "type_id": {
                                "type": "string",
                                "description": "The ID of the task type.",
                            },
                            "assigner_id": {
                                "type": "string",
                                "description": "The ID of the project member assigning the task.",
                            },
                        },
                        "required": [
                            "project_id",
                            "title",
                            "status_id",
                            "priority_id",
                            "type_id",
                            "assigner_id",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "update_task_status",
                    "description": "Update the status of an existing task.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "The ID of the task to update.",
                            },
                            "status_id": {
                                "type": "string",
                                "description": "The new status ID.",
                            },
                        },
                        "required": ["task_id", "status_id"],
                    },
                },
            },
        ]

    @track(name="execute_tool")
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:

        try:
            if name == "create_task":
                task_schema = TaskCreate(**arguments)
                result = self.task_service.add(task_schema)
                return {
                    "success": True,
                    "task": {"id": result.id, "title": result.title},
                }
            elif name == "update_task_status":
                task_id = arguments["task_id"]
                schema = TaskUpdate(status_id=arguments["status_id"])
                result = self.task_service.patch(task_id, schema)
                return {"success": True, "message": "Task status updated successfully."}
            raise ValueError(f"Tool {name} not found.")
        except Exception as e:
            return {"success": False, "error": str(e)}

    @track(entrypoint=True, name="run_agent_loop", project_name="Agentick")
    async def run_agent(
        self, project_id: str, prompt: str, history: List[AgentMessage]
    ) -> Dict[str, Any]:

        system_instruction = (
            "You are Agentick AI Assistant, a smart agent helping with project management. "
            f"You are working in Project ID: {project_id}. "
            "You can use tools to create, read, and update tasks on behalf of users. "
            "Always reply politely in Vietnamese. "
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
                "tools": self.tools,
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

                    tool_result = await self.execute_tool(func_name, func_args)

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
