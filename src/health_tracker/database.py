"""SQLAlchemy setup and database bootstrap helpers."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DATABASE_URL


class Base(DeclarativeBase):
    pass


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def initialize_database() -> None:
    # Import registers all ORM models before create_all reads metadata.
    from .models import db_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
