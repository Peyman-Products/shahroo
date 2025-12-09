import os
import sys

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db import engine
from app.models.permission import Role, Permission
from app.models.user import User, VerificationStatus

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

    # Create a default owner user if one doesn't exist
    owner_phone_number = "+989220171380"
    owner_user = db.query(User).filter(User.phone_number == owner_phone_number).first()

    if not owner_user:
        print("Creating default owner user...")
        owner_role = db.query(Role).filter(Role.name == "owner").first()
        if owner_role:
            new_owner = User(
                phone_number=owner_phone_number,
                role_id=owner_role.id,
                verification_status=VerificationStatus.verified
            )
            db.add(new_owner)
            db.commit()
            print("Default owner user created successfully.")
        else:
            print("Could not find the 'owner' role. Please run the migrations first.")
    else:
        print("Default owner user already exists.")

if __name__ == "__main__":
    main()
