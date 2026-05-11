from typing import Any, Dict, List
from app.schema.task_schema import TaskCreate, TaskUpdate
from app.services.task_service import TaskService
from opik import track


class TaskTools:
    def __init__(self, task_service: TaskService):
        self.task_service = task_service

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_task",
                    "description": (
                        "Create a new task within a project. Use this tool whenever a user asks to add, "
                        "assign, create, or schedule a task. Ensure all ID fields are absolute, exact UUID strings."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "The exact UUID string of the project where the task belongs.",
                            },
                            "title": {
                                "type": "string",
                                "description": "The concise, actionable title of the task.",
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed notes, requirements, or steps required for the task.",
                            },
                            "status_id": {
                                "type": "string",
                                "description": "The exact UUID of the task status (e.g., Todo, In Progress). Must be retrieved from context or project catalogs.",
                            },
                            "priority_id": {
                                "type": "string",
                                "description": "The exact UUID of the task priority (e.g., Low, Medium, High). Must be retrieved from context or project catalogs.",
                            },
                            "type_id": {
                                "type": "string",
                                "description": "The exact UUID of the task type (e.g., Feature, Bug, Task). Must be retrieved from context or project catalogs.",
                            },
                            "member_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "A list of exact user UUID strings representing the members assigned to this task.",
                            },
                            "started_at": {
                                "type": "string",
                                "description": "Optional ISO-8601 timestamp for when processing explicitly began.",
                            },
                            "due_date": {
                                "type": "string",
                                "description": "The task deadline/due date in ISO-8601 format.",
                            },
                            "estimated_hours": {
                                "type": "number",
                                "description": "The estimated number of hours required to complete this task.",
                            },
                        },
                        "required": [
                            "project_id",
                            "title",
                            "status_id",
                            "priority_id",
                            "type_id",
                            "due_date",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "update_task_status",
                    "description": "Update the status of an existing task to keep track of execution flow.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "The exact UUID of the task being updated.",
                            },
                            "status_id": {
                                "type": "string",
                                "description": "The exact UUID of the new task status.",
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
                    "task": {
                        "id": result.id,
                        "title": result.title,
                        "estimated_hours": result.estimated_hours,
                    },
                }
            elif name == "update_task_status":
                task_id = arguments["task_id"]
                schema = TaskUpdate(status_id=arguments["status_id"])
                result = self.task_service.patch(task_id, schema)
                return {"success": True, "message": "Task status updated successfully."}
            raise ValueError(f"Tool {name} not found.")
        except Exception as e:
            return {"success": False, "error": str(e)}
