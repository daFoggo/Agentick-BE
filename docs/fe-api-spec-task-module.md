# FE API Spec - Auth + Project Task Module

## 1. Base Information

- Base URL (local): `http://localhost:8000`
- API prefix: `/api/v1`
- Content type: `application/json`
- Auth method: Bearer JWT (`Authorization: Bearer <access_token>`)

Health check:
- `GET /api/v1/ping`

## 2. Standard Response Format

All successful responses use wrapper:

```json
{
  "success": true,
  "message": "Success",
  "data": {}
}
```

List responses (`FindResult`) shape:

```json
{
  "success": true,
  "message": "Success",
  "data": {
    "founds": [],
    "search_options": {
      "page": 1,
      "page_size": 20,
      "ordering": "-id",
      "total_count": 0
    }
  }
}
```

Error response (FastAPI default):

```json
{
  "detail": "..."
}
```

or validation error:

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Field required",
      "type": "missing"
    }
  ]
}
```

## 3. Common Query Params for List APIs

Available in most list endpoints:

- `page` (int, optional)
- `page_size` (int | "all", optional)
- `ordering` (string, optional)

`ordering` examples:
- `-id` (desc, default)
- `created_at`

## 4. Auth APIs

### 4.1 Sign Up
- `POST /api/v1/auth/sign-up`
- Auth: Not required

Request body:

```json
{
  "email": "user@example.com",
  "password": "123456",
  "name": "User Name",
  "avatar_url": "https://..." 
}
```

Response data (`UserInfo`):

```json
{
  "id": "uuid",
  "name": "User Name",
  "email": "user@example.com",
  "avatar_url": "https://...",
  "created_at": "2026-04-15T07:00:00+00:00"
}
```

### 4.2 Sign In
- `POST /api/v1/auth/sign-in`
- Auth: Not required

Request body:

```json
{
  "email__eq": "user@example.com",
  "password": "123456"
}
```

Response data (`SignInResponse`):

```json
{
  "access_token": "jwt",
  "expiration": "...",
  "refresh_token": "jwt",
  "refresh_expiration": "...",
  "user_info": {
    "id": "uuid",
    "name": "User Name",
    "email": "user@example.com",
    "avatar_url": null,
    "created_at": "2026-04-15T07:00:00+00:00"
  }
}
```

### 4.3 Refresh Token
- `POST /api/v1/auth/refresh`
- Auth: Not required

Request body:

```json
{
  "refresh_token": "jwt"
}
```

Response data (`TokenResponse`):

```json
{
  "access_token": "jwt",
  "expiration": "...",
  "refresh_token": "jwt",
  "refresh_expiration": "..."
}
```

## 5. Project-Scoped Task APIs

Base: `/api/v1/projects/{project_id}/tasks`

Auth: Required for all APIs below.

## 5.1 Task Schema

### TaskCreate

```json
{
  "project_id": "uuid (ignored by backend, path project_id is used)",
  "parent_id": "uuid | null",
  "title": "Task title",
  "description": "...",
  "status_id": "uuid",
  "type_id": "uuid",
  "priority_id": "uuid",
  "assigner_id": "project_member_id",
  "assignee_id": "project_member_id | null",
  "phase_id": "uuid | null",
  "start_date": "2026-04-15T08:00:00+00:00",
  "due_date": "2026-04-16T08:00:00+00:00",
  "order": 0
}
```

### TaskUpdate

```json
{
  "title": "optional",
  "description": "optional",
  "status_id": "optional",
  "type_id": "optional",
  "priority_id": "optional",
  "assigner_id": "optional",
  "assignee_id": "optional",
  "phase_id": "optional",
  "start_date": "optional datetime",
  "due_date": "optional datetime",
  "order": 1,
  "is_archived": true
}
```

### TaskRead

```json
{
  "id": "uuid",
  "created_at": "datetime",
  "updated_at": "datetime",
  "project_id": "uuid",
  "parent_id": "uuid | null",
  "title": "...",
  "description": "...",
  "status_id": "uuid",
  "type_id": "uuid",
  "priority_id": "uuid",
  "assigner_id": "uuid",
  "assignee_id": "uuid | null",
  "phase_id": "uuid | null",
  "start_date": "datetime",
  "due_date": "datetime",
  "order": 0,
  "is_archived": false,
  "is_deleted": false
}
```

## 5.2 Endpoints

- `POST /api/v1/projects/{project_id}/tasks`
- `GET /api/v1/projects/{project_id}/tasks`
- `GET /api/v1/projects/{project_id}/tasks/{task_id}`
- `PATCH /api/v1/projects/{project_id}/tasks/{task_id}`
- `DELETE /api/v1/projects/{project_id}/tasks/{task_id}` (soft delete: `is_deleted = true`)

Supported list filters (`TaskFind`):
- `id__eq`
- `title__ilike`
- `status_id__eq`
- `assignee_id__eq`
- `is_archived__eq`
- `is_deleted__eq`

## 6. Project Task Config APIs

Base: `/api/v1/projects/{project_id}/task-config`

Contains task metadata catalog per project:
- statuses
- types
- priorities
- tags

Auth: Required.

### 6.1 Status

Endpoints:
- `POST /statuses`
- `GET /statuses`
- `PATCH /statuses/{status_id}`
- `DELETE /statuses/{status_id}`

Schema (`TaskStatusCreate/Update`):

```json
{
  "project_id": "uuid (ignored by backend, path project_id is used)",
  "name": "To Do",
  "color": "#808080",
  "order": 0,
  "is_default": true,
  "is_completed": false
}
```

List filters (`TaskStatusFind`):
- `id__eq`
- `name__ilike`
- `is_default__eq`
- `is_completed__eq`

### 6.2 Type

Endpoints:
- `POST /types`
- `GET /types`
- `PATCH /types/{type_id}`
- `DELETE /types/{type_id}`

Schema (`TaskTypeCreate/Update`):

```json
{
  "project_id": "uuid (ignored by backend, path project_id is used)",
  "name": "Feature",
  "color": "#0066CC",
  "icon": "star",
  "order": 0,
  "is_default": true
}
```

List filters (`TaskTypeFind`):
- `id__eq`
- `name__ilike`
- `is_default__eq`

### 6.3 Priority

Endpoints:
- `POST /priorities`
- `GET /priorities`
- `PATCH /priorities/{priority_id}`
- `DELETE /priorities/{priority_id}`

Schema (`TaskPriorityCreate/Update`):

```json
{
  "project_id": "uuid (ignored by backend, path project_id is used)",
  "name": "High",
  "color": "#FF6600",
  "level": 2,
  "order": 2,
  "is_default": true
}
```

`level` range: `0..3`

List filters (`TaskPriorityFind`):
- `id__eq`
- `name__ilike`
- `level__eq`
- `is_default__eq`

### 6.4 Tag

Endpoints:
- `POST /tags`
- `GET /tags`
- `PATCH /tags/{tag_id}`
- `DELETE /tags/{tag_id}`

Schema (`TagCreate/Update`):

```json
{
  "project_id": "uuid (ignored by backend, path project_id is used)",
  "name": "Backend",
  "color": "#1E90FF"
}
```

List filters (`TagFind`):
- `id__eq`
- `name__ilike`

## 7. Project Phase APIs

Base: `/api/v1/projects/{project_id}/phases`

Auth: Required.

Endpoints:
- `POST /api/v1/projects/{project_id}/phases`
- `GET /api/v1/projects/{project_id}/phases`
- `GET /api/v1/projects/{project_id}/phases/{phase_id}`
- `PATCH /api/v1/projects/{project_id}/phases/{phase_id}`
- `DELETE /api/v1/projects/{project_id}/phases/{phase_id}`

Schema (`PhaseCreate/Update`):

```json
{
  "project_id": "uuid (ignored by backend, path project_id is used)",
  "name": "Sprint 1",
  "description": "optional",
  "order": 0,
  "start_date": "2026-04-15T08:00:00+00:00",
  "end_date": "2026-04-22T08:00:00+00:00"
}
```

List filters (`PhaseFind`):
- `id__eq`
- `name__ilike`

## 8. FE Integration Notes

1. All task-related APIs are now project-scoped.
2. Do not call old flat endpoints (`/tasks`, `/tags`, `/statuses`, ...). They were removed from routing.
3. For create APIs under project scope, backend enforces `project_id` from path (safe against cross-project payload).
4. Suggested FE boot flow:
   - Sign in -> get tokens
   - Get current user/team/project
   - Fetch task-config (statuses/types/priorities/tags)
   - Fetch phases
   - Fetch tasks

## 9. Suggested TypeScript Types (optional starter)

```ts
export type ApiResponse<T> = {
  success: boolean;
  message: string;
  data: T | null;
};

export type FindResult<T> = {
  founds: T[];
  search_options: {
    page?: number;
    page_size?: number | "all";
    ordering?: string;
    total_count?: number;
  };
};
```
