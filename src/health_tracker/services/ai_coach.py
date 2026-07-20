"""Gemini-powered health coaching suggestions."""

from __future__ import annotations

from ..config import GEMINI_API_KEY
from ..models.auth_model import get_user
from ..models.db_models import HealthLog, UserGoal
from ..models.goals_model import get_user_goal
from ..models.health_model import get_logs_in_range


def _fallback_advice(bmi: float | None, activity: int, goal: UserGoal) -> str:
    status = "chưa có BMI"
    tips = [
        "- Ăn: ưu tiên rau xanh, protein nạc, hạn chế đồ chiên và đường.",
        "- Uống: khoảng 2 lít nước/ngày, hạn chế nước ngọt.",
        f"- Tập: hướng tới ít nhất {goal.target_activity} phút vận động mỗi ngày.",
    ]
    if bmi is not None:
        if bmi < 18.5:
            status = "thiếu cân"
            tips[0] = "- Ăn: tăng calo lành mạnh (cơm, thịt, trứng, sữa, bơ, các loại hạt)."
            tips[2] = "- Tập: kết hợp đi bộ và tập sức mạnh nhẹ 3–4 buổi/tuần."
        elif bmi < 25:
            status = "bình thường"
            tips[0] = "- Ăn: duy trì khẩu phần cân bằng, đủ rau và protein."
        elif bmi < 30:
            status = "thừa cân"
            tips[0] = "- Ăn: giảm tinh bột tinh chế, tăng rau và đạm nạc."
            tips[2] = f"- Tập: cardio 30–45 phút, ít nhất {goal.target_activity} phút/ngày."
        else:
            status = "béo phì"
            tips[0] = "- Ăn: kiểm soát khẩu phần, ưu tiên thực phẩm ít calo mật độ cao."
            tips[2] = "- Tập: bắt đầu đi bộ nhanh 20–30 phút/ngày, tăng dần cường độ."
            tips.append("- Lưu ý: nên tham khảo ý kiến bác sĩ trước khi thay đổi chế độ mạnh.")
    if activity < goal.target_activity:
        tips.append(f"- Hôm nay mới {activity} phút vận động — hãy bổ sung đi bộ hoặc tại chỗ.")
    return (
        f"Gợi ý nhanh (chế độ offline) — tình trạng: {status}\n\n"
        + "\n".join(tips)
        + "\n\nDisclaimer: thông tin mang tính tham khảo, không thay thế tư vấn y tế."
    )


def generate_health_advice(user_id: int) -> str:
    user = get_user(user_id)
    if not user:
        raise RuntimeError("User profile not found.")

    logs = get_logs_in_range(user_id, 14)
    goal = get_user_goal(user_id)
    latest: HealthLog | None = logs[-1] if logs else None
    avg_activity = round(sum(log.activity_minutes for log in logs) / len(logs)) if logs else 0
    avg_weight = round(sum(log.weight for log in logs) / len(logs), 1) if logs else None

    if not GEMINI_API_KEY:
        return _fallback_advice(latest.bmi if latest else None, latest.activity_minutes if latest else 0, goal)

    profile_lines = [
        f"- Username: {user.username}",
        f"- Age: {user.age or 'unknown'}",
        f"- Gender: {user.gender or 'unknown'}",
        f"- Target weight: {goal.target_weight or 'not set'} kg",
        f"- Target activity: {goal.target_activity} minutes/day",
        f"- Target water: {goal.target_water} ml/day",
        f"- Max BMI goal: {goal.max_bmi}",
    ]
    if latest:
        profile_lines.extend(
            [
                f"- Latest weight: {latest.weight} kg",
                f"- Latest height: {latest.height} cm",
                f"- Latest BMI: {latest.bmi}",
                f"- Latest activity: {latest.activity_minutes} minutes",
                f"- Latest water: {latest.water_ml} ml",
                f"- Latest steps: {latest.steps}",
                f"- Latest heart rate: {latest.heart_rate or 'n/a'}",
                f"- Latest sleep: {latest.sleep_hours or 'n/a'} hours",
            ]
        )
    if avg_weight is not None:
        profile_lines.append(f"- 14-day average weight: {avg_weight} kg")
        profile_lines.append(f"- 14-day average activity: {avg_activity} minutes")

    prompt = f"""
You are a friendly Vietnamese health coach for a personal health tracking app.
Based on the user profile and recent logs, give practical advice in Vietnamese.

User data:
{chr(10).join(profile_lines)}

Respond in Vietnamese with these sections (use clear headings):
1) Tổng quan nhanh
2) Nên ăn gì hôm nay (3-5 gợi ý cụ thể)
3) Nên uống gì / lượng nước
4) Nên tập gì (20-40 phút, phù hợp tình trạng hiện tại)
5) Lưu ý an toàn

Keep it concise, actionable, and encouraging.
End with: "Disclaimer: không thay thế tư vấn y tế chuyên nghiệp."
""".strip()

    try:
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)
        last_error: Exception | None = None
        for model_name in ("gemini-flash-latest", "gemini-2.0-flash-lite", "gemini-2.0-flash"):
            try:
                response = client.models.generate_content(model=model_name, contents=prompt)
                text = getattr(response, "text", None) or str(response)
                if text.strip():
                    return text.strip()
            except Exception as exc:  # noqa: BLE001 - try next model
                last_error = exc
                continue
        raise RuntimeError(str(last_error) if last_error else "Empty AI response")
    except Exception as exc:  # noqa: BLE001 - surface a friendly offline fallback
        fallback = _fallback_advice(latest.bmi if latest else None, latest.activity_minutes if latest else 0, goal)
        return (
            f"{fallback}\n\n"
            f"(Gemini tạm thời không khả dụng: {exc.__class__.__name__}. Đã dùng gợi ý offline.)"
        )
