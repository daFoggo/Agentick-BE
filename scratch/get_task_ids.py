from sqlalchemy import select

from app.core.dependencies import get_database
from app.model.task import Task


def print_task_ids():
    print("Fetching task IDs from database...")
    db_ctx = get_database()
    with db_ctx.session() as session:
        tasks = session.scalars(select(Task)).all()
        if not tasks:
            print("No tasks found!")
            return
        for task in tasks:
            print(f'- Title: "{task.title}"')
            print(f"  ID: {task.id}")
            print(f"  Status: {task.status_id}")
            print(f"  Priority: {task.priority_id}")
            print()


if __name__ == "__main__":
    print_task_ids()
