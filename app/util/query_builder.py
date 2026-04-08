from typing import Any

from sqlalchemy import and_, true


IGNORED_KEYS = {"ordering", "page", "page_size", "total_count"}


def dict_to_sqlalchemy_filter_options(model: type, payload: dict[str, Any]):
    clauses = []

    for key, value in payload.items():
        if key in IGNORED_KEYS or value is None:
            continue

        field_name, _, operation = key.partition("__")
        operation = operation or "eq"

        column = getattr(model, field_name, None)
        if column is None:
            continue

        if operation == "eq":
            clauses.append(column == value)
        elif operation == "ne":
            clauses.append(column != value)
        elif operation == "lt":
            clauses.append(column < value)
        elif operation == "lte":
            clauses.append(column <= value)
        elif operation == "gt":
            clauses.append(column > value)
        elif operation == "gte":
            clauses.append(column >= value)
        elif operation == "like":
            clauses.append(column.like(value))
        elif operation == "ilike":
            clauses.append(column.ilike(value))
        elif operation == "in":
            in_values = value if isinstance(value, (list, tuple, set)) else [value]
            clauses.append(column.in_(in_values))
        elif operation == "isnull":
            clauses.append(column.is_(None) if value else column.is_not(None))

    if not clauses:
        return true()
    return and_(*clauses)