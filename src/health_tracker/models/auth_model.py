"""Authentication business logic."""

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from ..database import SessionLocal
from .db_models import User


def register_user(username: str, password: str, age: int | None, gender: str | None) -> User:
    username = username.strip()
    if not username or not password:
        raise ValueError("Username and password are required.")

    with SessionLocal() as session:
        try:
            if session.scalar(select(User).where(User.username == username)):
                raise ValueError("This username already exists.")
            user = User(username=username, password=password, age=age, gender=gender or None)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        except SQLAlchemyError as exc:
            session.rollback()
            raise RuntimeError("Could not create the account.") from exc


def authenticate(username: str, password: str) -> User | None:
    with SessionLocal() as session:
        try:
            return session.scalar(
                select(User).where(User.username == username.strip(), User.password == password)
            )
        except SQLAlchemyError as exc:
            raise RuntimeError("Could not sign in. Check the database connection.") from exc


def get_user(user_id: int) -> User | None:
    with SessionLocal() as session:
        try:
            return session.get(User, user_id)
        except SQLAlchemyError as exc:
            raise RuntimeError("Could not load user profile.") from exc
