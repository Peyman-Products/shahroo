# Database Migration and Seeding

This directory contains scripts for managing the database schema and data.

## Running the Migration

To run the database migration and seed the database with initial data, run the following command from the root of the project:

```bash
python scripts/run_migration.py
```

This script will:

1.  Create all tables in the database if they don't exist.
2.  Perform a data migration to move from the old `role` column to the new `role_id` column in the `users` table.
3.  Seed the database with initial roles and permissions if they don't already exist.
