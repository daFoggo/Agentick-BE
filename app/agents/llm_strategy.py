from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx


class LLMStrategy(ABC):
    @abstractmethod
    async def generate_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Sends chat messages and returns the standard response dict
        containing 'choices' (with message/content/tool_calls) and 'usage'.
        """
        pass


class OpenRouterStrategy(LLMStrategy):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    async def generate_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://agentick.ai",
            "X-OpenRouter-Title": "Agentick",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice
        if response_format:
            payload["response_format"] = response_format

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=45.0,
            )
            response.raise_for_status()
            return response.json()


class GeminiDirectStrategy(LLMStrategy):
    """
    Placeholder or simple implementation for a second strategy to satisfy
    the pattern requirement and show extensibility.
    """

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model

    async def generate_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        # Mock or real implementation placeholder
        # For demonstration we can throw NotImplementedError or return a mock
        raise NotImplementedError("GeminiDirectStrategy is ready for integration.")
