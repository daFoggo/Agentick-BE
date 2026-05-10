from app.repository.task_time_log_repository import TaskTimeLogRepository


class VelocityService:
    def __init__(self, task_time_log_repository: TaskTimeLogRepository):
        self.task_time_log_repository = task_time_log_repository

    def get_project_velocity_profile(self, project_id: str):
        # 1. Profile by User
        user_rows = self.task_time_log_repository.get_velocity_profile_by_user(
            project_id
        )
        by_user = [
            {
                "user_id": r[0],
                "user_name": r[1],
                "user_email": r[2],
                "total_hours": float(r[3]) if r[3] else 0.0,
                "log_count": r[4],
                "average_hours_per_log": float(r[3] / r[4]) if r[3] and r[4] else 0.0,
            }
            for r in user_rows
        ]

        # 2. Profile by Task Type
        type_rows = self.task_time_log_repository.get_velocity_profile_by_task_type(
            project_id
        )
        by_task_type = [
            {
                "type_id": r[0],
                "type_name": r[1],
                "type_color": r[2],
                "total_hours": float(r[3]) if r[3] else 0.0,
                "log_count": r[4],
            }
            for r in type_rows
        ]

        # 3. Profile by Day of the Week
        logs = self.task_time_log_repository.get_logs_for_project(project_id)

        day_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        day_stats = {
            i: {"day_name": day_names[i], "total_hours": 0.0, "log_count": 0}
            for i in range(7)
        }

        for logged_date, hours in logs:
            if logged_date:
                weekday = logged_date.weekday()  # 0 to 6
                day_stats[weekday]["total_hours"] += hours
                day_stats[weekday]["log_count"] += 1

        by_day_of_week = [
            {
                "day_index": i,
                "day_name": day_stats[i]["day_name"],
                "total_hours": day_stats[i]["total_hours"],
                "log_count": day_stats[i]["log_count"],
                "average_hours": (
                    day_stats[i]["total_hours"] / day_stats[i]["log_count"]
                )
                if day_stats[i]["log_count"] > 0
                else 0.0,
            }
            for i in range(7)
        ]

        return {
            "project_id": project_id,
            "by_user": by_user,
            "by_task_type": by_task_type,
            "by_day_of_week": by_day_of_week,
        }
