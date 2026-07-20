"""Threshold evaluation for health alerts."""

from __future__ import annotations

from dataclasses import dataclass

from .db_models import HealthLog, UserGoal


@dataclass
class Alert:
    level: str  # warning | info
    title: str
    message: str


def default_goal() -> UserGoal:
    """In-memory defaults when the user has not saved goals yet."""
    goal = UserGoal(
        user_id=0,
        target_weight=None,
        target_activity=30,
        target_water=2000,
        max_bmi=25.0,
    )
    return goal


def evaluate_alerts(
    *,
    bmi: float,
    weight: float,
    activity_minutes: int,
    water_ml: int = 0,
    heart_rate: int | None = None,
    sleep_hours: float | None = None,
    previous: HealthLog | None = None,
    goal: UserGoal | None = None,
) -> list[Alert]:
    """Return alerts when metrics cross standard or personal thresholds."""
    goal = goal or default_goal()
    alerts: list[Alert] = []

    if bmi < 18.5:
        alerts.append(Alert("warning", "BMI thấp", f"BMI {bmi}: thiếu cân. Nên tăng cường dinh dưỡng."))
    elif bmi >= 30:
        alerts.append(Alert("warning", "BMI nguy cơ cao", f"BMI {bmi}: béo phì. Nên tham khảo ý kiến y tế."))
    elif bmi >= goal.max_bmi:
        alerts.append(
            Alert(
                "warning",
                "BMI vượt ngưỡng",
                f"BMI {bmi} vượt mục tiêu tối đa {goal.max_bmi}. Kiểm soát ăn uống và tăng vận động.",
            )
        )

    if activity_minutes < goal.target_activity:
        alerts.append(
            Alert(
                "info",
                "Hoạt động chưa đạt mục tiêu",
                f"Hôm nay {activity_minutes} phút, mục tiêu {goal.target_activity} phút/ngày.",
            )
        )

    if water_ml and water_ml < goal.target_water:
        alerts.append(
            Alert(
                "info",
                "Uống nước chưa đủ",
                f"Đã uống {water_ml} ml, mục tiêu {goal.target_water} ml/ngày.",
            )
        )

    if goal.target_weight is not None and abs(weight - goal.target_weight) > 2:
        direction = "cao hơn" if weight > goal.target_weight else "thấp hơn"
        alerts.append(
            Alert(
                "info",
                "Cân nặng lệch mục tiêu",
                f"Cân nặng {weight:.1f} kg {direction} mục tiêu {goal.target_weight:.1f} kg hơn 2 kg.",
            )
        )

    if previous is not None:
        delta = abs(weight - previous.weight)
        if delta > 2:
            alerts.append(
                Alert(
                    "warning",
                    "Cân nặng biến động mạnh",
                    f"Thay đổi {delta:.1f} kg so với lần ghi gần nhất ({previous.weight:.1f} kg).",
                )
            )

    if heart_rate is not None and (heart_rate < 50 or heart_rate > 120):
        alerts.append(
            Alert(
                "warning",
                "Nhịp tim bất thường",
                f"Nhịp tim nghỉ {heart_rate} bpm nằm ngoài khoảng thường gặp (50–120).",
            )
        )

    if sleep_hours is not None and sleep_hours < 6:
        alerts.append(
            Alert(
                "info",
                "Ngủ chưa đủ",
                f"Chỉ ngủ khoảng {sleep_hours:.1f} giờ. Nên hướng tới 7–9 giờ/đêm.",
            )
        )

    return alerts
