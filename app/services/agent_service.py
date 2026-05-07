from typing import Any, Dict, List

from app.agents.custom_agent import CustomAgent
from app.schema.agent_schema import AgentMessage
from app.services.task_service import TaskService
from app.tools.task_tools import TaskTools


class AgentService:
    def __init__(self, task_service: TaskService):
        self.task_tools = TaskTools(task_service=task_service)
        self.agent = CustomAgent()

    async def run_agent(
        self, project_id: str, prompt: str, history: List[AgentMessage]
    ) -> Dict[str, Any]:
        return await self.agent.run(
            project_id=project_id,
            prompt=prompt,
            history=history,
            tools=self.task_tools.get_tool_definitions(),
            tool_executor=self.task_tools.execute_tool,
        )
