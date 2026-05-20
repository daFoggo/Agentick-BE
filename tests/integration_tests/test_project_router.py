from app.core.dependencies import get_current_active_user
from app.main import app
from app.model.project import Project
from app.model.project_member import ProjectMember
from app.model.task_priority import TaskPriority
from app.model.task_status import TaskStatus
from app.model.task_type import TaskType
from app.model.team import Team
from app.model.team_member import TeamMember
from app.model.user import User


def _create_project_tables(database):
    for model in (
        User,
        Team,
        TeamMember,
        Project,
        ProjectMember,
        TaskStatus,
        TaskType,
        TaskPriority,
    ):
        model.__table__.create(database._engine, checkfirst=True)


def test_create_project_api_creates_owner_and_default_catalogs(client, database):
    _create_project_tables(database)

    user = User(
        email="project-owner@example.com",
        name="Project Owner",
        hashed_password="not-used",
        user_token="project-owner-token",
        is_active=True,
        is_superuser=False,
    )
    team = Team(name="Owner Team", description=None, avatar_url=None, owner=user)
    team_member = TeamMember(team=team, user=user, role="owner")

    with database.session() as session:
        session.add_all([user, team, team_member])
        session.commit()
        user_id = user.id
        team_id = team.id

    def _get_current_user():
        with database.session() as session:
            return session.query(User).filter(User.id == user_id).first()

    app.dependency_overrides[get_current_active_user] = _get_current_user
    try:
        response = client.post(
            "/api/v1/projects",
            json={
                "team_id": team_id,
                "name": "API Created Project",
                "description": "Created through project API test",
            },
        )
    finally:
        app.dependency_overrides.pop(get_current_active_user, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["message"] == "Project created successfully"
    assert payload["data"]["name"] == "API Created Project"
    project_id = payload["data"]["id"]

    with database.session() as session:
        project_member = (
            session.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
            .one()
        )
        assert project_member.role == "owner"
        assert session.query(TaskStatus).filter_by(project_id=project_id).count() == 6
        assert session.query(TaskType).filter_by(project_id=project_id).count() == 5
        assert session.query(TaskPriority).filter_by(project_id=project_id).count() == 5
