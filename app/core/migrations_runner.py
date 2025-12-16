from pathlib import Path
from alembic import command
from alembic.config import Config

from app.core.config import settings


def run_migrations() -> None:
    """
    Ensure database schema is up-to-date by applying Alembic migrations.
    """
    project_root = Path(__file__).resolve().parents[2]
    alembic_cfg = Config(
        str(project_root / "alembic.ini"),
        config_args={"interpolation": None},
    )
    alembic_cfg.set_main_option("script_location", str(project_root / "migrations"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

    command.upgrade(alembic_cfg, "head")
