import os
import sys

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import engine, Base

def main():
    """
    Drops all tables in the database.
    """
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped successfully.")

if __name__ == "__main__":
    main()
