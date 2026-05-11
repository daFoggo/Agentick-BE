# 🗄️ Database & Models Rules

This guide outlines the database design principles, SQLAlchemy conventions, and model relationship standards for the **Agentick Backend** repository.

---

## 1. BaseModel Configuration

All database models must inherit from `BaseModel` (defined in `app/model/base_model.py`). This abstract base class automatically provides three essential auditing columns:

* **`id`**: `String(36)` - Primary key utilizing a randomly generated UUIDv4.
* **`created_at`**: `DateTime` - Stores the creation timestamp using database triggers/server-side defaults (`server_default`).
* **`updated_at`**: `DateTime` - Automatically updates on record modification via `onupdate`.

Never manually define these fields on individual models.

---

## 2. Primary Keys & Foreign Keys

* **No Integer IDs**: To prevent guessable URLs, scraping, and concurrency synchronization issues, always use UUIDv4 (`String(36)`) for both primary and foreign keys.
* **Explicit Foreign Key Constraints**: Always define explicit `ForeignKey` constraints with naming conventions and index them if they are frequently queried.
  ```python
  project_id = Column(String(36), ForeignKey("project.id", ondelete="CASCADE"), nullable=False, index=True)
  ```

---

## 3. Relationships & Cascade Deletes

* **Explicit Relationships**: Define `relationship()` on both ends of a foreign key relationship where appropriate to allow convenient ORM access.
* **Cascade Deletes**: Ensure that parent-child relationships have explicit cascade rules to prevent orphaned records in the database.
  * For composition (child cannot exist without parent): Use `cascade="all, delete-orphan"`.
  * For reference (child exists independently): Use `ondelete="SET NULL"` or `ondelete="RESTRICT"`.
* **Self-Referential Relations**: For hierarchical models (like `Task` and its `sub_tasks`), use explicit self-referential relationships:
  ```python
  parent_id = Column(String(36), ForeignKey("task.id", ondelete="CASCADE"), nullable=True)
  sub_tasks = relationship("Task", backref=backref("parent", remote_side=[id]))
  ```

---

## 4. Many-to-Many Association Tables

Many-to-many relationships must be handled through explicit association tables containing dual primary keys. Do not store arrays or comma-separated lists of IDs inside a single column.

Standard association tables/objects used:
1. **`task_tag`**: Maps `Task` ↔ `Tag`.
2. **`task_member`**: Model mapped to `task_member` table storing relation `Task` ↔ `User` with extra role context (`lead`/`member`).
3. **`event_participant`**: Maps `Event` ↔ `TeamMember`.

For standard M2M without extra attributes, use `Table`:
```python
task_tag = Table(
    "task_tag",
    BaseModel.metadata,
    Column("task_id", String(36), ForeignKey("task.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", String(36), ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True),
)
```

---

## 5. Soft Delete Pattern

To prevent accidental data loss, certain tables like `Project`, `Task`, and `Team` use a **Soft Delete** pattern:

* **Column**: `is_deleted = Column(Boolean, default=False, nullable=False)`
* **Deletion**: When a delete request is received, set `is_deleted = True` instead of calling `session.delete()`.
* **Queries**: Always filter out soft-deleted items when reading records.
  ```python
  # Always append the is_deleted filter:
  tasks = session.query(Task).filter(Task.project_id == project_id, Task.is_deleted.is_(False)).all()
  ```
