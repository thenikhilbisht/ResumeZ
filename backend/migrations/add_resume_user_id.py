import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import inspect, text

from app.core.database import engine


def migrate() -> None:
    if engine is None:
        raise RuntimeError("DATABASE_URL is not configured.")

    inspector = inspect(engine)
    columns = {
        column["name"]
        for column in inspector.get_columns("resumes")
    }

    if "user_id" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE resumes "
                    "ADD COLUMN user_id INTEGER NULL "
                    "REFERENCES users(id) ON DELETE CASCADE"
                )
            )
        print("Added nullable user_id column.")
    else:
        print("user_id column already exists.")

    with engine.begin() as connection:
        unassigned_count = connection.execute(
            text("SELECT COUNT(*) FROM resumes WHERE user_id IS NULL")
        ).scalar_one()

        if unassigned_count == 0:
            print("All resumes already have owners.")
            return

        user_count = connection.execute(
            text("SELECT COUNT(*) FROM users")
        ).scalar_one()

        if user_count != 1:
            print(
                f"{unassigned_count} resume(s) need an owner, "
                f"but {user_count} users exist. "
                "No resume ownership was changed."
            )
            return

        owner_id = connection.execute(
            text("SELECT id FROM users")
        ).scalar_one()

        connection.execute(
            text(
                "UPDATE resumes SET user_id = :owner_id "
                "WHERE user_id IS NULL"
            ),
            {"owner_id": owner_id},
        )

        print(
            f"Assigned {unassigned_count} existing resume(s) "
            f"to user ID {owner_id}."
        )

    with engine.connect() as connection:
        remaining = connection.execute(
            text("SELECT COUNT(*) FROM resumes WHERE user_id IS NULL")
        ).scalar_one()

    print(f"Unassigned resumes remaining: {remaining}")


if __name__ == "__main__":
    migrate()
