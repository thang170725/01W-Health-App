"""Simulated wearable integration tab."""

from __future__ import annotations # Hỗ trợ gợi ý kiểu dữ liệu (type hinting) linh hoạt hơn cho các phiên bản Python.

import random
import tkinter as tk
from tkinter import messagebox, ttk

from ...models.health_model import create_health_log, get_latest_log


class DeviceTab(ttk.Frame):
    def __init__(self, parent: tk.Misc, user_id: int, on_sync) -> None:
        super().__init__(parent, padding=18)
        self.user_id = user_id
        self.on_sync = on_sync # Hàm callback truyền từ màn hình chính, có nhiệm vụ bắn dữ liệu vừa giả lập sang DashboardTab (Tab Nhập liệu).
        self.device_var = tk.StringVar(value="FitBand Pro") # Lưu tên thiết bị được chọn (mặc định chọn "FitBand Pro").
        self.last_sync_var = tk.StringVar(value="Chưa đồng bộ lần nào trong phiên này.") # Biến hiển thị thời gian sync gần nhất
        self.status_var = tk.StringVar(value="Sẵn sàng giả lập kết nối thiết bị.") # trạng thái thanh tiến trình.
        self._pending: dict | None = None # Biến tạm lưu gói dữ liệu vừa tạo ra

        # dựng giao diện UI
        # Tạo tiêu đề lớn và đoạn văn hướng dẫn cách dùng tab này với độ rộng tối đa 700px.
        ttk.Label(self, text="Giả lập đồng bộ thiết bị đo", font=("Arial", 14, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            self,
            text=(
                "Dùng tab này để lấy bước chân, nhịp tim, giấc ngủ (user không cần nhớ/đo tay). "
                "“Đồng bộ vào form” sẽ đổ cân nặng + vận động sang tab Nhập liệu; "
                "các chỉ số cảm biến hiện ở khung “Từ thiết bị”."
            ),
            wraplength=700,
        ).grid(row=1, column=0, sticky="w", pady=(6, 14))

        # Tạo khung LabelFrame chứa ô danh sách thả xuống (Combobox).
        form = ttk.LabelFrame(self, text="Thiết bị", padding=14)
        form.grid(row=2, column=0, sticky="ew")
        ttk.Label(form, text="Chọn thiết bị").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            form,
            textvariable=self.device_var,
            values=("FitBand Pro", "Smart Scale X", "Health Watch Mini"), # 3 tùy chọn tên thiết bị: "FitBand Pro", "Smart Scale X", "Health Watch Mini". 
            state="readonly", # Khoá không cho gõ chữ (state="readonly").
            width=24,
        ).grid(row=0, column=1, sticky="w", padx=(10, 0))

        # Thanh tiến trình Progressbar chạy từ 0 đến 100 để tạo hiệu ứng "Đang kết nối Bluetooth / Đang tải dữ liệu".
        # Dòng chữ status_var báo trạng thái dưới thanh tiến trình.
        self.progress = ttk.Progressbar(form, mode="determinate", maximum=100, length=320)
        self.progress.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(14, 6))
        ttk.Label(form, textvariable=self.status_var).grid(row=2, column=0, columnspan=2, sticky="w")

        # Tạo 2 nút bấm hành động đặt cạnh nhau:
        # "Đồng bộ vào form nhập liệu": Bắn dữ liệu sang tab bên cạnh để người dùng xem/sửa rồi mới bấm lưu sau.
        # "Đồng bộ & lưu ngay": Bắn dữ liệu sang tab kia đồng thời lưu thẳng vào DB luôn.
        # Các Label phía dưới hiển thị thông tin xem trước (preview) dữ liệu vừa sync.
        actions = ttk.Frame(self)
        actions.grid(row=3, column=0, sticky="w", pady=(16, 0))
        ttk.Button(actions, text="Đồng bộ vào form nhập liệu", command=self.sync_to_form).pack(side="left")
        ttk.Button(actions, text="Đồng bộ & lưu ngay", command=self.sync_and_save).pack(side="left", padx=(8, 0))

        ttk.Label(self, textvariable=self.last_sync_var, wraplength=700).grid(
            row=4, column=0, sticky="w", pady=(18, 0)
        )
        self.preview_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.preview_var, justify="left").grid(row=5, column=0, sticky="w", pady=(8, 0))

    # LOGIC GIẢ LẬP DỮ LIỆU VÀ HIỆU ỨNG ANIMATION
    # Hàm sinh dữ liệu ngẫu nhiên (_generate_payload)
    # Lấy cân nặng gần nhất làm chuẩn, rồi cộng/trừ ngẫu nhiên $\pm 0.5\text{ kg}$ để tạo cảm giác cân nặng biến thiên thực tế.
    # Dùng random.randint và random.uniform để random bước chân ($2500 - 12000$), 
    # nhịp tim ($58 - 105\text{ bpm}$), giấc ngủ ($5.5 - 8.5\text{ giờ}$), 
    # nước uống ($800 - 2800\text{ ml}$).Đóng gói toàn bộ vào một dictionary kèm tên thiết bị vừa chọn.
    def _generate_payload(self) -> dict:
        latest = get_latest_log(self.user_id)
        weight = round((latest.weight if latest else 65.0) + random.uniform(-0.5, 0.5), 1)
        height = latest.height if latest else 170.0
        activity = random.randint(20, 90)
        steps = random.randint(2500, 12000)
        heart_rate = random.randint(58, 105)
        sleep_hours = round(random.uniform(5.5, 8.5), 1)
        water_ml = random.randint(800, 2800)
        return {
            "weight": weight,
            "height": height,
            "activity_minutes": activity,
            "steps": steps,
            "heart_rate": heart_rate,
            "sleep_hours": sleep_hours,
            "water_ml": water_ml,
            "source": "device",
            "device_name": self.device_var.get(),
        }

    # Hiệu ứng chạy thanh Progressbar (_animate)
    # Hàm đệ quy đếm thời gian bằng self.after(28, ...) (sau mỗi $28\text{ ms}$ tăng $5\%$ thanh tiến trình).
    # Trong lúc chạy, chuyển đổi trạng thái chữ: Đang kết nối... $\rightarrow$ Đang đọc cảm biến... $\rightarrow$ Đang truyền dữ liệu... $\rightarrow$ Đồng bộ hoàn tất.
    # Khi đạt $100\%$, gọi hàm on_done() để xử lý logic tiếp theo.
    def _animate(self, on_done) -> None:
        self.progress["value"] = 0
        self.status_var.set(f"Đang kết nối {self.device_var.get()}...")

        def tick(value: int = 0) -> None:
            self.progress["value"] = value
            if value >= 100:
                self.status_var.set("Đồng bộ hoàn tất.")
                on_done()
                return
            if value == 35:
                self.status_var.set("Đang đọc cảm biến...")
            elif value == 70:
                self.status_var.set("Đang truyền dữ liệu...")
            self.after(28, lambda: tick(value + 5))

        tick()

    # In kết quả xem trước (_show_preview)
    # Format lại dữ liệu thành dạng văn bản danh sách để in ra màn hình cho người dùng kiểm tra.
    def _show_preview(self, payload: dict) -> None:
        self.preview_var.set(
            "Gói dữ liệu giả lập:\n"
            f"- Thiết bị: {payload['device_name']}\n"
            f"- Cân nặng: {payload['weight']} kg | Chiều cao: {payload['height']} cm\n"
            f"- Hoạt động: {payload['activity_minutes']} phút | Bước chân: {payload['steps']}\n"
            f"- Nhịp tim: {payload['heart_rate']} bpm | Ngủ: {payload['sleep_hours']} giờ\n"
            f"- Nước uống ước tính: {payload['water_ml']} ml"
        )
        self.last_sync_var.set(
            f"Lần sync gần nhất: {payload['device_name']} — {payload['weight']} kg, "
            f"{payload['activity_minutes']} phút hoạt động."
        )

    # XỬ LÝ 2 NÚT ĐỒNG BỘ
    # Nút sync_to_form (Chỉ đẩy dữ liệu sang Form)
    # Chạy animation $\rightarrow$ Tạo payload ngẫu nhiên $\rightarrow$ Gọi self.on_sync(...) để điền dữ liệu sang tab Dashboard $\rightarrow$ Hiển thị thông báo thành công.
    # Nút sync_and_save (Đẩy dữ liệu sang Form + Lưu ngay vào DB)
    # Chạy animation $\rightarrow$ Tạo payload $\rightarrow$ Gọi create_health_log(...) để lưu luôn vào DB $\rightarrow$ Bắn dữ liệu sang tab Dashboard đồng thời báo thông báo (và pop-up cảnh báo nếu chỉ số vượt ngưỡng nguy hiểm).
    def sync_to_form(self) -> None:
        def finish() -> None:
            try:
                payload = self._generate_payload()
                self._pending = payload
                self._show_preview(payload)
                self.on_sync(
                    payload["weight"],
                    payload["height"],
                    payload["activity_minutes"],
                    steps=payload["steps"],
                    heart_rate=payload["heart_rate"],
                    sleep_hours=payload["sleep_hours"],
                    water_ml=payload["water_ml"],
                )
                messagebox.showinfo(
                    "Đồng bộ xong",
                    "Dữ liệu thiết bị đã sẵn sàng ở tab Nhập liệu. Hãy kiểm tra rồi lưu.",
                )
            except RuntimeError as exc:
                messagebox.showerror("Không đồng bộ được", str(exc))

        self._animate(finish)

    def sync_and_save(self) -> None:
        def finish() -> None:
            try:
                payload = self._generate_payload()
                self._show_preview(payload)
                log, alerts = create_health_log(
                    self.user_id,
                    payload["weight"],
                    payload["height"],
                    payload["activity_minutes"],
                    steps=payload["steps"],
                    heart_rate=payload["heart_rate"],
                    sleep_hours=payload["sleep_hours"],
                    water_ml=payload["water_ml"],
                    source="device",
                )
                self.on_sync(
                    payload["weight"],
                    payload["height"],
                    payload["activity_minutes"],
                    steps=payload["steps"],
                    heart_rate=payload["heart_rate"],
                    sleep_hours=payload["sleep_hours"],
                    water_ml=payload["water_ml"],
                )
                warn_text = ""
                warnings = [a for a in alerts if a.level == "warning"]
                if warnings:
                    warn_text = "\n\nCảnh báo:\n" + "\n".join(f"- {a.title}: {a.message}" for a in warnings)
                messagebox.showinfo(
                    "Đã lưu từ thiết bị",
                    f"Đã lưu bản ghi BMI {log.bmi}.{warn_text}",
                )
                if warnings:
                    messagebox.showwarning(
                        "Cảnh báo vượt ngưỡng",
                        "\n\n".join(f"{a.title}\n{a.message}" for a in warnings),
                    )
            except (ValueError, RuntimeError) as exc:
                messagebox.showerror("Không lưu được", str(exc))

        self._animate(finish)
