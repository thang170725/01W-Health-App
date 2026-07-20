"""SQLAlchemy ORM entities."""

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)

    health_logs: Mapped[list["HealthLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    goal: Mapped["UserGoal | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )


class HealthLog(Base):
    __tablename__ = "health_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    height: Mapped[float] = mapped_column(Float, nullable=False)
    bmi: Mapped[float] = mapped_column(Float, nullable=False)
    activity_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    heart_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sleep_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    water_ml: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)

    user: Mapped[User] = relationship(back_populates="health_logs")


class UserGoal(Base):
    __tablename__ = "user_goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    target_weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_activity: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    target_water: Mapped[int] = mapped_column(Integer, default=2000, nullable=False)
    max_bmi: Mapped[float] = mapped_column(Float, default=25.0, nullable=False)

    user: Mapped[User] = relationship(back_populates="goal")
