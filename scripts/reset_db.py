import os
import sys

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect, text

from app.core.config import settings

def main():
    """
    Drops all tables in the database.
    """
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)

    # Get all table names
    table_names = inspector.get_table_names()

    with engine.connect() as connection:
        with connection.begin() as transaction:
            for table_name in reversed(inspector.get_table_names()):
                print(f"Dropping table {table_name}...")
                connection.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;'))
    print("All tables dropped successfully.")

if __name__ == "__main__":
    main()
