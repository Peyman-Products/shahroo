# Database Migrations

This directory contains the database migration scripts, managed by Alembic.

## Creating a New Migration

To create a new migration script after making changes to the models, run the following command from the root of the project:

```bash
alembic revision --autogenerate -m "Your migration message"
```

This will generate a new migration script in the `migrations/versions` directory.

## Applying Migrations

To apply the latest migrations to the database, run the following command:

```bash
alembic upgrade head
```
