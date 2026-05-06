from pydantic import BaseModel
from typing import List, Optional


class AgentMessage(BaseModel):
    role: str  # 'system', 'user', 'assistant', 'tool'
    content: Optional[str] = None
    name: Optional[str] = None
    tool_call_id: Optional[str] = None


class AgentChatRequest(BaseModel):
    project_id: str
    message: str
    history: Optional[List[AgentMessage]] = []


class AgentChatResponse(BaseModel):
    response: str
    tool_calls_executed: List[str]
