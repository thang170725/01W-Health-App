"""User goals CRUD."""

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from ..database import SessionLocal
from .db_models import UserGoal
from .thresholds import default_goal


def get_user_goal(user_id: int) -> UserGoal:
    with SessionLocal() as session:
        try:
            goal = session.scalar(select(UserGoal).where(UserGoal.user_id == user_id))
            if goal:
                return goal
            fallback = default_goal()
            fallback.user_id = user_id
            return fallback
        except SQLAlchemyError as exc:
            raise RuntimeError("Could not load user goals.") from exc


def save_user_goal(
    user_id: int,
    *,
    target_weight: float | None,
    target_activity: int,
    target_water: int,
    max_bmi: float,
) -> UserGoal:
    if target_activity <= 0:
        raise ValueError("Target activity must be greater than zero.")
    if target_water <= 0:
        raise ValueError("Target water must be greater than zero.")
    if max_bmi <= 0:
        raise ValueError("Max BMI must be greater than zero.")
    if target_weight is not None and target_weight <= 0:
        raise ValueError("Target weight must be greater than zero.")

    with SessionLocal() as session:
        try:
            goal = session.scalar(select(UserGoal).where(UserGoal.user_id == user_id))
            if goal is None:
                goal = UserGoal(user_id=user_id)
                session.add(goal)
            goal.target_weight = target_weight
            goal.target_activity = target_activity
            goal.target_water = target_water
            goal.max_bmi = max_bmi
            session.commit()
            session.refresh(goal)
            return goal
        except SQLAlchemyError as exc:
            session.rollback()
            raise RuntimeError("Could not save user goals.") from exc
