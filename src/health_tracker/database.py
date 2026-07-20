"""SQLAlchemy setup and database bootstrap helpers."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DATABASE_URL


class Base(DeclarativeBase):
    pass


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def _column_exists(connection, table: str, column: str) -> bool:
    result = connection.execute(
        text(
            """
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table
              AND COLUMN_NAME = :column
            """
        ),
        {"table": table, "column": column},
    )
    return bool(result.scalar())


def migrate_schema() -> None:
    """Add new columns/tables for upgrades without dropping existing data."""
    alterations = [
        ("health_logs", "steps", "ALTER TABLE health_logs ADD COLUMN steps INT NOT NULL DEFAULT 0"),
        ("health_logs", "heart_rate", "ALTER TABLE health_logs ADD COLUMN heart_rate INT NULL"),
        ("health_logs", "sleep_hours", "ALTER TABLE health_logs ADD COLUMN sleep_hours FLOAT NULL"),
        ("health_logs", "water_ml", "ALTER TABLE health_logs ADD COLUMN water_ml INT NOT NULL DEFAULT 0"),
        ("health_logs", "source", "ALTER TABLE health_logs ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT 'manual'"),
    ]
    with engine.begin() as connection:
        for table, column, ddl in alterations:
            if not _column_exists(connection, table, column):
                connection.execute(text(ddl))


def initialize_database() -> None:
    # Import registers all ORM models before create_all reads metadata.
    from .models import db_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    migrate_schema()
