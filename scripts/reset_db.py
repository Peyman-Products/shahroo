import os
import sys

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect, text

from app.core.config import settings

def main():
    """
    Drops all tables and custom types in the database.
    """
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)

    with engine.connect() as connection:
        with connection.begin() as transaction:
            # Drop all tables
            print("Dropping all tables...")
            for table_name in reversed(inspector.get_table_names()):
                connection.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;'))

            # Drop all custom ENUM types
            print("Dropping all custom ENUM types...")
            result = connection.execute(text("SELECT typname FROM pg_type WHERE typtype = 'e'"))
            for row in result:
                connection.execute(text(f'DROP TYPE IF EXISTS "{row[0]}" CASCADE;'))

    print("All tables and custom types dropped successfully.")

if __name__ == "__main__":
    main()
