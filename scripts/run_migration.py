import os
import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from app.db import Base, engine
from app.models.permission import Role, Permission
from app.models.user import User

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def main():
    """
    Runs the database migration and seeds the database with initial data.
    """
    db = Session(bind=engine)
    inspector = inspect(engine)

    # Create all tables if they don't exist
    Base.metadata.create_all(bind=engine)

    # Check if the old 'role' column exists in the 'users' table
    columns = [col['name'] for col in inspector.get_columns('users')]
    if 'role' in columns and 'role_id' not in columns:
        print("Running data migration...")

        # Add the 'role_id' column to the 'users' table
        db.execute(text('ALTER TABLE users ADD COLUMN role_id INTEGER'))

        # Seed the roles
        owner_role = Role(name="owner")
        admin_role = Role(name="admin")
        user_role = Role(name="user")

        db.add_all([owner_role, admin_role, user_role])
        db.commit()

        # Update the 'role_id' column based on the old 'role' column
        db.execute(text("UPDATE users SET role_id = (SELECT id FROM roles WHERE name = users.role)"))

        # Remove the old 'role' column
        db.execute(text('ALTER TABLE users DROP COLUMN role'))

        db.commit()

        print("Data migration completed successfully.")
    else:
        print("Data migration not required.")

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
