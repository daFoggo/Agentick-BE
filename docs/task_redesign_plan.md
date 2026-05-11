# Implementation Plan — Agentick Task System Redesign

This document outlines the systematic approach to refactoring and migrating the Task system based on "deadline-driven" behavioral patterns.

---

## 📊 Phase 1: Database Migration (Schema Updates)

### 1.1. Task Table Modifications
Modify `app/model/task.py` and create corresponding migration script via Alembic.
- **DROP Column**: `assigner_id` (FK to `project_member`)
- **DROP Column**: `start_date` (TIMESTAMPTZ NULLABLE)
- **ADD Column**: `started_at` (TIMESTAMPTZ NULLABLE) — Records when user hits "Start".
- **ADD Column**: `completed_at` (TIMESTAMPTZ NULLABLE) — Records manual or auto completion.

### 1.2. Task Member Transition (Replacing `task_assignee`)
- **Deprecate**: `task_assignee` relationship table.
- **CREATE Model**: `app/model/task_member.py`
  ```python
  class TaskMember(BaseModel):
      __tablename__ = "task_member"
      task_id: Mapped[str] = mapped_column(ForeignKey("task.id", ondelete="CASCADE"))
      user_id: Mapped[str] = mapped_column(ForeignKey("user.id")) # Reference to user
      role: Mapped[str] = mapped_column(String(20), default="member") # 'lead', 'member'
      joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
  ```
- **Migration Logic**: Port data from `task_assignee` to `task_member` with `role='member'`. Use existing `assigner_id` to create `task_member` with `role='lead'`.

### 1.3. Unified Activity Log Redesign
Refactor `app/model/task_activity.py` to unify changelogs, comments, and milestones.
- **ADD Column**: `activity_type` (VARCHAR) — `comment`, `field_change`, `started`, `completed`, etc.
- **ADD Column**: `content` (TEXT) — For storing comment content.
- **ADD Column**: `mentioned_user_ids` (ARRAY of VARCHAR).
- **CREATE TABLE (Optional)**: `activity_reaction` for tracking emoji responses.

### 1.4. Expand Task Checkpoint
Update `app/model/task_checkpoint.py`.
- **ADD Column**: `checkpoint_type` (VARCHAR) — `progress`, `started`, `completed`, `manual_end`.

---

## ⚙️ Phase 2: Backend Logic & API Refactor

### 2.1. Schemas Updates (`app/schema/task_schema.py`)
- Remove `start_date` and `assigner_id` from `TaskCreate` / `TaskUpdate`.
- Add `started_at` and `completed_at` to `TaskRead`.
- Update `TaskCreate` to optionally take `member_ids` instead of `assignee_ids`.

### 2.2. Repository Layer (`app/repository/task_repository.py`)
- Update `create` method to automatically insert the acting user into `task_member` table as `role='lead'`.
- Modify `get_my_tasks_complex` to query across new `task_member` linkages instead of `assigner_id` OR `assignees`.
- Refactor activity tracking inside `update` to populate the new structured format in `TaskActivity`.

### 2.3. Domain Services (`app/services/task_service.py`)
- **Implement `start_task(task_id, user_id)`**:
  1. Set `task.started_at = now()`.
  2. Insert `TaskCheckpoint(type='started', progress_pct=0)`.
  3. Insert `TaskActivity(type='started')`.
- **Implement `complete_task(task_id, completed_at, user_id)`**:
  1. Set `task.completed_at = completed_at or now()`.
  2. Update task status to a value where `is_completed=True`.
  3. Insert `TaskCheckpoint(type='completed', progress_pct=100)`.
- **Expose via Endpoints** in `app/api/v1/endpoints/tasks.py`:
  - `POST /tasks/{id}/start`
  - `PATCH /tasks/{id}/complete`

---

## 🤖 Phase 3: Agent Redesign (Risk & Outreach)

### 3.1. Morning Scan: "Silent Risk" Logic
Modify `app/services/risk_analysis_service.py`:
- **Condition**: If `due_date` within next 2 days AND `started_at IS NULL`.
- **Impact**: Automatically inject +0.3 to baseline risk score.
- **Metric Adjust**: When `started_at` is NULL, calculate `effective_hours` by examining `available_working_hours` remaining until `due_date`, multiplied by (1 / (1 + user_historical_buffer_ratio)).

### 3.2. Agent Outreach Pipeline
Modify `app/services/agent_outreach_service.py`:
- **Trigger 1 (Stale)**: Only remind if `started_at IS NOT NULL` AND there is no activity within the last 24h.
- **Trigger 2 (New)**: Trigger alert if `due_date <= 2 days` AND `started_at IS NULL`.
- **Trigger 3 (New)**: Trigger reminder if status `is_completed=true` BUT `completed_at` has been NULL for more than 2 hours.
- **Anti-Spam Logic**: Suppress outreach execution if any `TaskActivity` from the user occurred within the last 4 hours.

---

## 🎨 Phase 4: Frontend Alignment (Agentick-FE)

### 4.1. Form Enhancements
- Update Task Creator/Editor components:
  - Remove "Start Date" inputs entirely.
  - Adjust `due_date` picker: Default time to **23:59** on selection unless specified.
  - Rebuild the Members Panel: Display the creator with a "Lead" badge dynamically, remove specific Assigner dropdowns.

### 4.2. Task Detail Timeline & Logic
- Render contextual timeline states based on `started_at`:
  - **Pre-Start**: Shows huge "▶ Start Task" action.
  - **Active**: Renders dynamic "Running for X days" duration.
  - **Completed**: Displays time linked to `completed_at` with interactive "Edit completion time" tool.

### 4.3. Unified Activity Feed
- Consolidate activity logic to fetch from the unified feed.
- Implement markdown/avatar visual separation for:
  - Milestone markers (Started/Done) -> Distinct styling/icons.
  - Standard Comments (Replies, Reactions).
  - Property/Audit trail items (Lighter, condensed text).

### 4.4. BigCalendar Integration
Update formatting to the 3-mode logic:
- **Deadline Pins**: `started_at` is NULL. 30 min block at `due_date` end-of-day.
- **Active Ranges**: Renders block FROM `started_at` TO `due_date` (Dashed/Gradient styles).
- **Completed Shading**: Active block FROM `started_at` TO `completed_at`. Hidden by default.

---

## ✅ Next Steps Checklist

1. [ ] Generate Alembic Migration script for Task schema refactoring.
2. [ ] Replace static `task_assignee` in `app/model/task.py` with new `TaskMember` class.
3. [ ] Update all downstream queries relying on `assigner_id` or `start_date`.
4. [ ] Implement `/start` and `/complete` endpoints in Service and Router layers.
5. [ ] Apply logic overrides in `RiskAnalysisService` and `AgentOutreachService`.
6. [ ] Validate across the frontend codebase.
