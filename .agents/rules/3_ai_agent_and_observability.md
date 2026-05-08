# 🤖 AI Agent & Observability Rules

This guide defines the engineering principles, API integrations, and observability standards for the **AI Agent** within the **Agentick Backend** repository.

Our agent system is built based on **Anthropic's "Building Effective Agents"** industry best practices to ensure reliability, predictability, and safety in production.

---

## 1. Core Engineering Principles

### 1.1. Simplicity Over Heavy Frameworks
* **Principle**: Avoid heavy, opaque Agent Frameworks (like LangChain, CrewAI) that abstract away raw prompts, introduce overhead, and complicate debugging.
* **Implementation**: We maintain complete control by building our own **ReAct loop** and calling **OpenRouter** directly via `httpx` in `CustomAgent`. Prompts must be kept readable, transparent, and direct.

### 1.2. Programmatic Gates (Hybrid Code-AI Control)
* **Principle**: Never use LLM reasoning to evaluate strict conditions that can be evaluated using deterministic Python code. Calling LLMs is slow, expensive, and non-deterministic.
* **Implementation**: For the **Agent Outreach** system, checking whether to contact a member must be evaluated deterministically via Python code inside `AgentOutreachService` (checking active states, soft-delete, active time log within 24h, etc.). The LLM is invoked **only at the very end** to write the personalized copy/email.

### 1.3. ACI (Agent-Computer Interface) & Poka-Yoke Design
* **Principle**: Design tools (JSON Schemas) with the same care as API endpoints. Use defensive design ("Poka-yoke" / mistake-proofing) so the LLM cannot physically supply incorrect parameters.
* **Implementation**:
  * **No Implicit Defaults**: Specify formats explicitly (e.g., `ISO-8601` for `start_date` and `due_date` fields).
  * **Strict Types**: Always require absolute **UUIDv4 format** strings for foreign keys (`status_id`, `priority_id`, `type_id`, `project_id`) rather than raw names to avoid LLM hallucination.
  * **Include Metadata**: Always include fields like `estimated_hours` directly inside task creation tools to establish early baseline data for risk forecasting.

---

## 2. LLM Configuration (OpenRouter)

We use **OpenRouter** for dynamic model selection, prioritizing high-performance, cost-effective models.

### Environment Requirements (`.env`)
```env
OPENROUTER_API_KEY=your_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-oss-120b:free
```

---

## 3. Observability & Tracing (Opik)

We integrate **Opik Observability** to capture traces, spans, token consumption, and execution time of LLM steps and tool calls.

### 3.1. Decorating Traces & Spans
Always use Opik's `@track` decorator to log execution trees:

* **Trace Entry Point (Parent)**: Use `@track(entrypoint=True)` on the main function triggering the agent.
  ```python
  from opik import track

  @track(entrypoint=True, name="run_agent_loop", project_name="Agentick")
  def run_agent(self, user_message: str):
      # ...
  ```
* **Tool Call (Child Span)**: Use `@track` on functions executing external tools to link them as child spans.
  ```python
  @track(name="execute_tool")
  def execute_tool(self, tool_name: str, arguments: dict):
      # ...
  ```

### 3.2. Local Debugging via Agent Playground
To debug agent behavior locally with live pairing, use Opik's tunnel endpoint:
```bash
uv run opik endpoint --project "Agentick" -- uv run uvicorn app.main:app --port 8000 --reload
```
This enables the **Status: Paired ✔ (Connected)** state on the Opik Web UI, enabling live interaction and prompt engineering.
