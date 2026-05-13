# AI Agent Runtime

The AI runtime should stay simple, observable, and deterministic where possible.

## Core Rule

Use deterministic Python for strict business logic. Use the LLM only for tasks that benefit from language generation, interpretation, summarization, or flexible reasoning.

Examples that should be deterministic:

- Permission checks.
- Soft-delete checks.
- Active/inactive user checks.
- Date windows for scheduled outreach.
- Filtering tasks before asking the LLM to analyze or write copy.

Examples that may use the LLM:

- Generating personalized outreach copy.
- Interpreting natural-language task creation requests.
- Producing a risk explanation after deterministic data is collected.

## LLM Strategy

Provider access belongs behind `app/agents/llm_strategy.py`.

- Use `LLMStrategy` for the interface.
- Use `OpenRouterStrategy` for OpenRouter calls.
- Do not scatter direct provider HTTP calls across services or tools.
- Keep provider swap decisions isolated to the strategy layer or its factory.

## Tool Design

LLM tools are API surfaces. Treat their schemas carefully.

- Required fields must be explicit.
- Foreign keys should be UUID strings, not display names.
- Date fields should specify ISO format expectations.
- Enum-like values should be constrained or clearly documented.
- Tool execution should validate input before writing data.

## JSON Robustness

LLM output can be malformed. Application workflows should not crash solely because model JSON is syntactically imperfect.

When parsing model output, prefer staged recovery:

1. Parse normally.
2. Clean common formatting defects.
3. Extract known fields with strict fallbacks where the workflow allows it.
4. Raise a controlled application error if the output is unusable.

## Scheduler

Scheduler lifecycle belongs in `app/core/scheduler.py` and starts through FastAPI lifespan.

Rules:

- Do not start scheduler jobs at import time.
- Use fresh database sessions for independent background units of work.
- Bound concurrency when processing many tasks or users.
- Keep external calls timeout-aware.
- Log enough context to diagnose failed scheduled runs.

## Observability

Use Opik tracing for agent workflows that involve LLM calls or tool execution.

- Main agent entry points should be traceable.
- Tool execution should be traceable when practical.
- Do not log secrets, full tokens, or sensitive user content unnecessarily.
