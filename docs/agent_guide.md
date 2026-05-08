# 🤖 AI Agent & Opik Observability Configuration Guide

This document provides a detailed guide on how to set up, configure, and monitor the **AI Agent** within the **Agentick Backend** project using **OpenRouter** and **Opik Observability (Traces, Spans & Agent Playground)**.

---

## 1. Configuring the AI Agent with OpenRouter

The Agentick project utilizes **OpenRouter** to dynamically invoke Large Language Models (LLMs), prioritizing the free open-source model `openai/gpt-oss-120b:free`.

### Environment Variable Setup `.env`
Add the following environment variables to the end of your `.env` file:
```env
# --- AI AGENT CONFIGURATION (OPENROUTER) ---
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-oss-120b:free
```

### Running the Standalone OpenRouter Test
To verify if your connection to OpenRouter is working correctly, run the following standalone test script:
```bash
uv run scratch/test_openrouter.py
```
*The script will automatically load the `.env` variables and make a test call to OpenRouter.*

---

## 2. Configuring LLM Observability with Opik

**Opik** is a leading LLM observability and performance optimization platform by Comet. It helps track the full lifecycle of LLM calls (Traces) and individual tool invocation actions (Spans) of the Agent in detail.

### Opik Environment Variables
Configure the following lines in your `.env` file:
```env
# --- OPIK LLM OBSERVABILITY CONFIGURATION ---
OPIK_API_KEY=your_opik_api_key_here
OPIK_PROJECT_NAME=Agentick
```

### Step 1: Login and Configure Opik
Run the following command in the project root and follow the terminal instructions to link your Opik account:
```bash
uv run opik configure
```
*Enter the API Key from your Opik account (found under Opik Settings).*

### Step 2: Activating the Agent Playground (Tunnel Connection)
To use the interactive **Agent Playground** on Opik's Web interface (which allows you to chat, fine-tune prompts, and switch models online), you need to establish a secure tunnel connection from Opik Cloud back to your local server.

Run the following command in a new PowerShell or Terminal window to launch the server with the tunnel:
```bash
uv run opik endpoint --project "Agentick" -- uv run uvicorn app.main:app --port 8000 --reload
```
**Result:** The Opik Web interface will display the status **Status: Paired ✔ (Connected)**. You can now chat and experiment with prompts directly in the browser!

---

## 3. How It Works in Code

### Registering the `@track` Decorator
In the file [agent_service.py](file:///d:/Dev%20projects/Agentick-BE/app/services/agent_service.py), Opik `@track` decorators are pre-integrated:

* **Parent Trace (Entry Point)**: The `run_agent()` function is wrapped with `@track(entrypoint=True, name="run_agent_loop", project_name="Agentick")`.
* **Child Span (Tool Execution)**: The `execute_tool()` function is wrapped with `@track(name="execute_tool")` to log tool executions that create or modify tasks in the database.

When invoking the `/api/v1/agent/chat` API or running tests, Opik automatically visualizes a **Span Tree** showing processing duration, token costs, and tool execution results.

---

## 4. Agent Design Philosophy & Optimization (Based on Anthropic's "Building Effective Agents")

The Agent system in **Agentick** is designed, optimized, and operated according to industry-leading principles from Anthropic to ensure high reliability, exceptional performance, and cost efficiency in production environments.

### 4.1. Simplicity Over Heavy Frameworks
* **Anthropic Rule**: Avoid using heavy agent frameworks (such as LangChain or CrewAI) when not necessary, as they introduce abstract layers that obscure actual prompts and make debugging difficult.
* **How Agentick Applies This**:
  * We build our own ReAct loop and directly connect to OpenRouter using the `httpx` library in `CustomAgent`.
  * **Programmatic Gates**: With the **Agent Outreach** feature, instead of asking the LLM to reason whether it should send an email (which wastes tokens and is error-prone), we use pure Python code in `AgentOutreachService` to evaluate conditions (e.g., check if the task is in todo/done status, if the deadline is further than 3 days, if an email was sent in the last 24 hours, or if the member has been active in the last 2 hours). The LLM is only called at the final step when artificial intelligence is genuinely required to write personalized email copy.

### 4.2. Agent-Computer Interface (ACI) Optimization & Error-Proofing (Poka-Yoke)
* **Anthropic Rule**: Define tools (JSON Schema) for the LLM with the same meticulous care as writing documentation for a junior developer. Optimize parameters to ensure the LLM never passes incorrect data types (Poka-yoke).
* **How Agentick Applies This**:
  * We reviewed and restructured the entire tool catalog in [task_tools.py](file:///d:/Dev%20projects/Agentick-BE/app/tools/task_tools.py).
  * Resolved missing required field errors by including `start_date` and `due_date` directly in the `create_task` schema with explicit **ISO-8601** format instructions.
  * Explicitly specified **absolute UUIDv4 format** for foreign key fields (`status_id`, `priority_id`, `type_id`, `project_id`) to prevent the LLM from hallucinating or passing arbitrary text strings.
  * Integrated the `estimated_hours` field directly into the Tool schema, encouraging the AI to actively log estimated duration upon task creation to serve as baseline data for the deadline risk prediction system.

### 4.3. Prioritizing Transparency
* **Anthropic Rule**: Help users understand the planning steps and thought process of the Agent to build long-term trust.
* **How Agentick Applies This**:
  * The entire thought process (Thoughts) and tool execution actions are automatically captured using Opik's `@track` decorator and saved directly in the database.
  * Detailed risk signals are stored as JSON in the `signals` field of the `risk_snapshot` table to be displayed on the frontend, showing project managers exactly *why* the Agent flagged a task as high risk.

### 4.4. Evaluator-Optimizer Workflow
* **Anthropic Rule**: Use a generator LLM to produce outputs and an evaluator LLM (or feedback loop) to check and refine results, significantly increasing output quality.
* **How Agentick Applies This**:
  * In the advanced deadline risk analysis workflow, Agentick leverages historical execution data—specifically the variance between initial estimates (`estimated_hours`) and actual execution time (`actual_hours`)—as a feedback loop to let the Agent calibrate the `risk_score` before generating warnings.
