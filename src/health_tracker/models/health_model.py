"""Health log CRUD and BMI calculation logic."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from ..database import SessionLocal
from .db_models import HealthLog


def calculate_bmi(weight: float, height_cm: float) -> float:
    if weight <= 0 or height_cm <= 0:
        raise ValueError("Weight and height must be greater than zero.")
    return round(weight / (height_cm / 100) ** 2, 1)


def bmi_recommendation(bmi: float) -> tuple[str, str, bool]:
    if bmi < 18.5:
        return "Underweight", "Increase nutritious meals and maintain a balanced routine.", False
    if bmi < 25:
        return "Normal", "Great. Keep your current healthy routine.", False
    if bmi < 30:
        return "Overweight", "Control meals and increase regular physical activity.", True
    return "Obese", "Health warning: consider consulting a medical professional.", True


def create_health_log(user_id: int, weight: float, height: float, activity_minutes: int) -> HealthLog:
    if activity_minutes < 0:
        raise ValueError("Activity minutes cannot be negative.")
    bmi = calculate_bmi(weight, height)
    with SessionLocal() as session:
        try:
            log = HealthLog(
                user_id=user_id, log_date=date.today(), weight=weight, height=height,
                bmi=bmi, activity_minutes=activity_minutes,
            )
            session.add(log)
            session.commit()
            session.refresh(log)
            return log
        except SQLAlchemyError as exc:
            session.rollback()
            raise RuntimeError("Could not save the health record.") from exc


def get_health_logs(user_id: int) -> list[HealthLog]:
    with SessionLocal() as session:
        try:
            return list(session.scalars(
                select(HealthLog).where(HealthLog.user_id == user_id).order_by(HealthLog.log_date)
            ))
        except SQLAlchemyError as exc:
            raise RuntimeError("Could not load health history.") from exc


def delete_health_log(user_id: int, log_id: int) -> None:
    with SessionLocal() as session:
        try:
            log = session.scalar(select(HealthLog).where(HealthLog.id == log_id, HealthLog.user_id == user_id))
            if not log:
                raise ValueError("Selected record no longer exists.")
            session.delete(log)
            session.commit()
        except SQLAlchemyError as exc:
            session.rollback()
            raise RuntimeError("Could not delete the health record.") from exc


def get_latest_log(user_id: int) -> HealthLog | None:
    with SessionLocal() as session:
        return session.scalar(
            select(HealthLog).where(HealthLog.user_id == user_id).order_by(HealthLog.log_date.desc(), HealthLog.id.desc())
        )
