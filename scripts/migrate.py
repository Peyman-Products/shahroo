import os
import sys
from sqlalchemy import create_engine, inspect
from app.db import Base
from app.models import user, permission  # Ensure all models are imported

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def main():
    """
    Creates all tables in the database.
    """
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

if __name__ == "__main__":
    main()
