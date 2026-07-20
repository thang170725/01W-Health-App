"""Health log CRUD and BMI calculation logic."""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from ..database import SessionLocal
from .db_models import HealthLog
from .goals_model import get_user_goal
from .thresholds import Alert, evaluate_alerts


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


def create_health_log(
    user_id: int,
    weight: float,
    height: float,
    activity_minutes: int,
    *,
    steps: int = 0,
    heart_rate: int | None = None,
    sleep_hours: float | None = None,
    water_ml: int = 0,
    source: str = "manual",
) -> tuple[HealthLog, list[Alert]]:
    if activity_minutes < 0:
        raise ValueError("Activity minutes cannot be negative.")
    if steps < 0:
        raise ValueError("Steps cannot be negative.")
    if water_ml < 0:
        raise ValueError("Water intake cannot be negative.")
    if heart_rate is not None and heart_rate <= 0:
        raise ValueError("Heart rate must be greater than zero.")
    if sleep_hours is not None and sleep_hours < 0:
        raise ValueError("Sleep hours cannot be negative.")

    bmi = calculate_bmi(weight, height)
    previous = get_latest_log(user_id)
    goal = get_user_goal(user_id)
    alerts = evaluate_alerts(
        bmi=bmi,
        weight=weight,
        activity_minutes=activity_minutes,
        water_ml=water_ml,
        heart_rate=heart_rate,
        sleep_hours=sleep_hours,
        previous=previous,
        goal=goal,
    )

    with SessionLocal() as session:
        try:
            log = HealthLog(
                user_id=user_id,
                log_date=date.today(),
                weight=weight,
                height=height,
                bmi=bmi,
                activity_minutes=activity_minutes,
                steps=steps,
                heart_rate=heart_rate,
                sleep_hours=sleep_hours,
                water_ml=water_ml,
                source=source,
            )
            session.add(log)
            session.commit()
            session.refresh(log)
            return log, alerts
        except SQLAlchemyError as exc:
            session.rollback()
            raise RuntimeError("Could not save the health record.") from exc


def preview_alerts(
    user_id: int,
    weight: float,
    height: float,
    activity_minutes: int,
    *,
    water_ml: int = 0,
    heart_rate: int | None = None,
    sleep_hours: float | None = None,
) -> tuple[float, list[Alert]]:
    bmi = calculate_bmi(weight, height)
    alerts = evaluate_alerts(
        bmi=bmi,
        weight=weight,
        activity_minutes=activity_minutes,
        water_ml=water_ml,
        heart_rate=heart_rate,
        sleep_hours=sleep_hours,
        previous=get_latest_log(user_id),
        goal=get_user_goal(user_id),
    )
    return bmi, alerts


def get_health_logs(user_id: int) -> list[HealthLog]:
    with SessionLocal() as session:
        try:
            return list(
                session.scalars(
                    select(HealthLog).where(HealthLog.user_id == user_id).order_by(HealthLog.log_date, HealthLog.id)
                )
            )
        except SQLAlchemyError as exc:
            raise RuntimeError("Could not load health history.") from exc


def get_logs_in_range(user_id: int, days: int) -> list[HealthLog]:
    cutoff = date.today() - timedelta(days=days - 1)
    return [log for log in get_health_logs(user_id) if log.log_date >= cutoff]


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
            select(HealthLog)
            .where(HealthLog.user_id == user_id)
            .order_by(HealthLog.log_date.desc(), HealthLog.id.desc())
        )


def get_summary(user_id: int) -> dict:
    logs = get_health_logs(user_id)
    latest = logs[-1] if logs else None
    week = [log for log in logs if log.log_date >= date.today() - timedelta(days=6)]
    goal = get_user_goal(user_id)
    streak = 0
    cursor = date.today()
    dated = {log.log_date for log in logs}
    while cursor in dated:
        streak += 1
        cursor -= timedelta(days=1)
    activity_hits = sum(1 for log in week if log.activity_minutes >= goal.target_activity)
    return {
        "latest": latest,
        "total_logs": len(logs),
        "week_count": len(week),
        "streak": streak,
        "activity_goal_rate": round(100 * activity_hits / max(len(week), 1)),
        "goal": goal,
    }
