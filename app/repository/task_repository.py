from app.repository.base_repository import BaseRepository
from app.model.task import Task
from app.model.project_member import ProjectMember
from app.core.exceptions import NotFoundError


class TaskRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(session_factory, Task)

    def create(self, schema, auto_commit=True):
        data = schema.model_dump() if hasattr(schema, "model_dump") else schema
        assignee_ids = data.pop("assignee_ids", [])
        with self.session_factory() as session:
            item = self.model(**data)
            if assignee_ids:
                assignees = session.query(ProjectMember).filter(ProjectMember.id.in_(assignee_ids)).all()
                item.assignees = assignees
            session.add(item)
            if auto_commit:
                session.commit()
                session.refresh(item)
            else:
                session.flush()
            return item

    def update(self, id, schema, auto_commit=True):
        data = schema.model_dump(exclude_none=True) if hasattr(schema, "model_dump") else schema
        assignee_ids = data.pop("assignee_ids", None)
        with self.session_factory() as session:
            item = session.query(self.model).filter(self.model.id == id).first()
            if not item:
                raise NotFoundError(detail=f"not found id : {id}")
            
            for key, value in data.items():
                setattr(item, key, value)
            
            if assignee_ids is not None:
                assignees = session.query(ProjectMember).filter(ProjectMember.id.in_(assignee_ids)).all()
                item.assignees = assignees
            
            if auto_commit:
                session.commit()
                session.refresh(item)
            return item
    def read_by_options(self, schema, eager: bool = False):
        data = schema.model_dump(exclude_none=True) if hasattr(schema, "model_dump") else schema
        team_id = data.pop("team_id__eq", None)
        
        with self.session_factory() as session:
            from app.model.project import Project
            from app.util.query_builder import dict_to_sqlalchemy_filter_options
            from sqlalchemy.orm import joinedload
            from app.core.config import settings
            
            ordering = data.get("ordering", settings.ORDERING)
            order_query = (
                getattr(self.model, ordering[1:]).desc()
                if ordering.startswith("-")
                else getattr(self.model, ordering).asc()
            )
            page = data.get("page", settings.PAGE)
            page_size = data.get("page_size", settings.PAGE_SIZE)
            
            filter_options = dict_to_sqlalchemy_filter_options(self.model, data)
            query = session.query(self.model)
            
            if team_id:
                query = query.join(Project, Project.id == self.model.project_id).filter(Project.team_id == team_id)
            
            if eager:
                for eager_attr in getattr(self.model, "eagers", []):
                    query = query.options(joinedload(getattr(self.model, eager_attr)))
            
            filtered_query = query.filter(filter_options)
            query = filtered_query.order_by(order_query)
            
            if page_size == "all":
                results = query.all()
            else:
                results = query.limit(page_size).offset((page - 1) * page_size).all()
            
            total_count = filtered_query.count()
            return {
                "founds": results,
                "search_options": {
                    "page": page,
                    "page_size": page_size,
                    "ordering": ordering,
                    "total_count": total_count,
                },
            }
