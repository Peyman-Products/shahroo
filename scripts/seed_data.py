import os
import sys
from sqlalchemy.orm import Session
from app.db import engine
from app.models.permission import Permission

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """
    Seeds the database with initial data.
    """
    db = Session(bind=engine)

    # Seed the database with initial permissions if they don't exist
    if not db.query(Permission).first():
        print("Seeding permissions...")

        # Create permissions
        create_task_permission = Permission(name="create_task")
        db.add(create_task_permission)
        db.commit()

        print("Permissions seeded successfully.")
    else:
        print("Permissions already seeded.")

if __name__ == "__main__":
    main()
