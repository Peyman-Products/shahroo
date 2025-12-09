import os
import sys
from sqlalchemy.orm import Session
from app.db import engine
from app.models.permission import Role, Permission

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """
    Seeds the database with initial data.
    """
    db = Session(bind=engine)

    # Seed the database with initial roles and permissions if they don't exist
    if not db.query(Role).first():
        print("Seeding database...")

        # Create roles
        owner_role = Role(name="owner")
        admin_role = Role(name="admin")
        user_role = Role(name="user")

        db.add_all([owner_role, admin_role, user_role])
        db.commit()

        # Create permissions
        create_task_permission = Permission(name="create_task")
        db.add(create_task_permission)
        db.commit()

        # Assign permissions to roles
        admin_role.permissions.append(create_task_permission)
        db.commit()

        print("Database seeded successfully.")
    else:
        print("Database already seeded.")

if __name__ == "__main__":
    main()
