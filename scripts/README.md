# Database Seeding

This directory contains scripts for seeding the database with initial data.

## Running the Seeding Script

To seed the database with initial roles and permissions, run the following command from the root of the project:

```bash
python scripts/seed_data.py
```

This script will populate the database with the initial roles (`owner`, `admin`, `user`) and permissions (`create_task`) if they don't already exist.
