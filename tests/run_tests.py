import pytest
import sys
import os

from dotenv import load_dotenv

if __name__ == "__main__":
    # Add the project root to the Python path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, project_root)

    # Load the .env.test file
    load_dotenv(dotenv_path=os.path.join(project_root, '.env.test'))

    # Run pytest
    sys.exit(pytest.main())
