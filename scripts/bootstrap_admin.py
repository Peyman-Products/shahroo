import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.bootstrap.admin import bootstrap_admin
from app.core.config import settings
from app.db import SessionLocal


def main() -> None:
    if not settings.BOOTSTRAP_ADMIN_PHONE:
        raise ValueError("BOOTSTRAP_ADMIN_PHONE is not set")

    db = SessionLocal()
    try:
        bootstrap_admin(
            db,
            settings.BOOTSTRAP_ADMIN_PHONE,
            settings.BOOTSTRAP_ADMIN_FORCE,
        )
        print("✅ Admin bootstrap done")
    finally:
        db.close()


if __name__ == "__main__":
    main()
