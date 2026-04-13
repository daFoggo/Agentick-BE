from app.core.dependencies import get_database
from app.model.user import User

def check_users():
    db_instance = get_database()
    with db_instance.session() as session:
        users = session.query(User).all()
        print(f"Total users: {len(users)}")
        for u in users:
            print(f"ID: {u.id}, Email: {u.email}, Name: {u.name}")

if __name__ == "__main__":
    check_users()
