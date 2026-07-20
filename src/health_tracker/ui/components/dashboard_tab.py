"""Input, summary cards, goals, and threshold alerts."""

import tkinter as tk
from tkinter import messagebox, ttk

from ...models.goals_model import save_user_goal
from ...models.health_model import (
    bmi_recommendation,
    create_health_log,
    get_summary,
    preview_alerts,
)
from ...models.thresholds import Alert


class DashboardTab(ttk.Frame):
    def __init__(self, parent: tk.Misc, user_id: int, on_data_changed) -> None:
        super().__init__(parent, padding=12)
        self.user_id = user_id
        self.on_data_changed = on_data_changed  # được gọi khi dữ liệu thay đổi để báo cho các tab khác như Biểu đồ hay Lịch sử cập nhật lại

        # Manual fields (user types these)
        # khai báo các biến dữ liệu form nhập tay
        self.weight_var = tk.StringVar()
        self.height_var = tk.StringVar()
        self.activity_var = tk.StringVar(value="30")
        self.water_var = tk.StringVar()

        # Device-only extras (filled by Smart Wearable sync, not typed by hand)
        # khai báo các biến nhân từ thiết bị giả lập IoT
        self.steps_var = tk.StringVar(value="—") # bước chân
        self.heart_var = tk.StringVar(value="—") # nhịp tim
        self.sleep_var = tk.StringVar(value="—") # giấc ngủ
        self.device_note_var = tk.StringVar(    # biến thông báo
            value="Chưa có dữ liệu thiết bị. Vào tab “Thiết bị giả lập” để đồng bộ."
        )
        self._device_payload: dict | None = None # chứa dict dữ liệu thô đồng bộ từ thiết bị

        # khai báo các biến hiển thị kết quả và thổng quan
        self.result_var = tk.StringVar(value="Nhập cân nặng, chiều cao và phút vận động.")
        self.alert_var = tk.StringVar(value="Chưa có cảnh báo.")

        self.summary_bmi = tk.StringVar(value="—")
        self.summary_weight = tk.StringVar(value="—")
        self.summary_streak = tk.StringVar(value="0 ngày")
        self.summary_goal = tk.StringVar(value="0%")

        self.target_weight_var = tk.StringVar()
        self.target_activity_var = tk.StringVar(value="30")
        self.target_water_var = tk.StringVar(value="2000")
        self.max_bmi_var = tk.StringVar(value="25.0")

        self._build()   # gọi hàm để vẽ giao diện
        self.refresh_summary() # gọi hàm để nạp dữ liệu từ DB vào giao diện ngay khi mở app

    def _build(self) -> None:
        # cấu hình màn hình chia thành 2 cột rộng bằng nhau
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # khung tổng quan nhanh (4 thẻ nhỏ ở trên cùng)
        cards = ttk.LabelFrame(self, text="Tổng quan nhanh", padding=10)
        cards.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        for col in range(4):
            cards.columnconfigure(col, weight=1)
        self._card(cards, 0, "BMI mới nhất", self.summary_bmi)
        self._card(cards, 1, "Cân nặng", self.summary_weight)
        self._card(cards, 2, "Streak ghi nhận", self.summary_streak)
        self._card(cards, 3, "Đạt mục tiêu tuần", self.summary_goal)

        # form "nhật ký hôm nay" (nhập tay) - cột bên trái
        form = ttk.LabelFrame(self, text="Nhật ký hôm nay (nhập tay)", padding=12)
        form.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        ttk.Label(
            form,
            text="Chỉ cần 3 chỉ số chính. Nước uống để trống nếu không chắc.",
            font=("Arial", 10),
            wraplength=360,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        manual_fields = (
            ("Cân nặng (kg)", self.weight_var),
            ("Chiều cao (cm)", self.height_var),
            ("Vận động hôm nay (phút)", self.activity_var),
            ("Nước uống ước tính (ml)", self.water_var),
        )
        for row, (label, variable) in enumerate(manual_fields, start=1):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
            ttk.Entry(form, textvariable=variable, width=18).grid(row=row, column=1, sticky="ew", pady=4)

        # Thêm dòng gợi ý nhỏ và 2 nút bấm: "Tính BMI & kiểm tra" (gọi hàm calculate) và "Lưu bản ghi" (gọi hàm save).
        ttk.Label(form, text="Gợi ý: đi bộ 30 phút ≈ 30 | chạy 20 phút ≈ 20").grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(2, 0)
        )

        buttons = ttk.Frame(form)
        buttons.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(buttons, text="Tính BMI & kiểm tra", command=self.calculate).pack(side="left")
        ttk.Button(buttons, text="Lưu bản ghi", command=self.save).pack(side="right")

        # khung "chỉ số từ thiết bị" - con của form nhập tay
        # Hiển thị các dữ liệu đọc từ thiết bị thông minh (Bước chân, Nhịp tim, Giấc ngủ) dạng nhãn (Label) chứ không cho sửa tay, kèm nút bấm để xóa dữ liệu thiết bị nếu muốn.
        device_box = ttk.LabelFrame(form, text="Chỉ số từ thiết bị (tự động)", padding=10)
        device_box.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        ttk.Label(device_box, textvariable=self.device_note_var, wraplength=340).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 6)
        )
        for row, (label, variable) in enumerate(
            (
                ("Bước chân", self.steps_var),
                ("Nhịp tim (bpm)", self.heart_var),
                ("Giấc ngủ (giờ)", self.sleep_var),
            ),
            start=1,
        ):
            ttk.Label(device_box, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=2)
            ttk.Label(device_box, textvariable=variable, font=("Segoe UI", 10, "bold")).grid(
                row=row, column=1, sticky="w", pady=2
            )
        ttk.Button(device_box, text="Xóa dữ liệu thiết bị khỏi form", command=self.clear_device_data).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )

        # cột bên phải (mục tiêu & cảnh báo)
        # Vẽ Form "Mục tiêu cá nhân" cho phép chỉnh sửa mục tiêu cân nặng, phút tập, nước uống, BMI trần.
        # Vẽ khung "Cảnh báo ngưỡng" để in danh sách các cảnh báo (như BMI quá cao, tập luyện quá ít...).
        # Đặt Label self.result_var ở dưới cùng để thông báo trạng thái chung
        side = ttk.Frame(self)
        side.grid(row=1, column=1, sticky="nsew", padx=(6, 0))
        side.columnconfigure(0, weight=1)

        goals = ttk.LabelFrame(side, text="Mục tiêu cá nhân", padding=12)
        goals.grid(row=0, column=0, sticky="ew")
        goal_fields = (
            ("Cân nặng mục tiêu (kg)", self.target_weight_var),
            ("Vận động mục tiêu (phút/ngày)", self.target_activity_var),
            ("Nước mục tiêu (ml/ngày)", self.target_water_var),
            ("BMI tối đa chấp nhận", self.max_bmi_var),
        )
        for row, (label, variable) in enumerate(goal_fields):
            ttk.Label(goals, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
            ttk.Entry(goals, textvariable=variable, width=12).grid(row=row, column=1, sticky="ew", pady=3)
        ttk.Button(goals, text="Lưu mục tiêu", command=self.save_goals).grid(
            row=len(goal_fields), column=0, columnspan=2, sticky="ew", pady=(10, 0)
        )

        alerts = ttk.LabelFrame(side, text="Cảnh báo ngưỡng", padding=12)
        alerts.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        ttk.Label(alerts, textvariable=self.alert_var, wraplength=320, justify="left").grid(sticky="nw")

        ttk.Label(self, textvariable=self.result_var, wraplength=860, justify="left").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(10, 0)
        )

    # hàm phụ vẽ thẻ card
    # Hàm nhỏ giúp vẽ nhanh một thẻ gồm 1 dòng chữ tiêu đề nhỏ phía trên và 1 số liệu lớn in đậm phía dưới
    def _card(self, parent: ttk.LabelFrame, column: int, title: str, variable: tk.StringVar) -> None:
        frame = ttk.Frame(parent, padding=6)
        frame.grid(row=0, column=column, sticky="ew", padx=4)
        ttk.Label(frame, text=title, font=("Segoe UI", 9)).pack(anchor="w")
        ttk.Label(frame, textvariable=variable, font=("Segoe UI", 14, "bold")).pack(anchor="w")

    # CÁC HÀM XỬ LÝ LOGIC BACKEND & DỮ LIỆU
    # Nạp dữ liệu tổng quan (refresh_summary)
    def refresh_summary(self) -> None:
        try:
            summary = get_summary(self.user_id) # Gọi get_summary() từ database. Lấy bản ghi mới nhất điền vào 4 thẻ tổng quan ở trên và nạp dữ liệu mục tiêu cá nhân vào các ô input tương ứng
            latest = summary["latest"]
            self.summary_bmi.set(f"{latest.bmi:.1f}" if latest else "—")
            self.summary_weight.set(f"{latest.weight:.1f} kg" if latest else "—")
            self.summary_streak.set(f"{summary['streak']} ngày")
            self.summary_goal.set(f"{summary['activity_goal_rate']}%")
            goal = summary["goal"]
            self.target_weight_var.set("" if goal.target_weight is None else str(goal.target_weight))
            self.target_activity_var.set(str(goal.target_activity))
            self.target_water_var.set(str(goal.target_water))
            self.max_bmi_var.set(str(goal.max_bmi))
        except RuntimeError as exc:
            messagebox.showerror("Không tải được tổng quan", str(exc))

    # Validate dữ liệu nhập tay (_manual_values & _save_payload)
    # Chuyển chuỗi từ các ô Entry sang kiểu số (float, int). Nếu người dùng gõ chữ, hàm tung ra ValueError.
    def _manual_values(self) -> dict:
        try:
            water_raw = self.water_var.get().strip()
            return {
                "weight": float(self.weight_var.get()),
                "height": float(self.height_var.get()),
                "activity_minutes": int(self.activity_var.get()),
                "water_ml": int(water_raw) if water_raw else 0,
            }
        except ValueError as exc:
            raise ValueError("Cân nặng, chiều cao và phút vận động phải là số hợp lệ.") from exc

    # Đóng gói dữ liệu tổng hợp từ cả phần nhập tay và phần thiết bị IoT (nếu có đồng bộ) thành 1 dictionary chuẩn bị gửi lưu vào DB.
    def _save_payload(self) -> dict:
        values = self._manual_values()
        if self._device_payload:
            # Keep manual overrides for weight/height/activity/water if user edited them,
            # but attach sensor fields from the last device sync.
            values["steps"] = int(self._device_payload.get("steps", 0))
            values["heart_rate"] = self._device_payload.get("heart_rate")
            values["sleep_hours"] = self._device_payload.get("sleep_hours")
            if not self.water_var.get().strip() and self._device_payload.get("water_ml"):
                values["water_ml"] = int(self._device_payload["water_ml"])
            values["source"] = "device"
        else:
            values["steps"] = 0
            values["heart_rate"] = None
            values["sleep_hours"] = None
            values["source"] = "manual"
        return values

    # Hiển thị cảnh báo (_show_alerts)
    # In các dòng cảnh báo ra khung "Cảnh báo ngưỡng". Nếu có cảnh báo mức nguy hiểm (warning), bật thêm cửa sổ Pop-up messagebox.showwarning để cảnh báo trực tiếp người dùng
    def _show_alerts(self, alerts: list[Alert]) -> None:
        if not alerts:
            self.alert_var.set("Tất cả chỉ số trong ngưỡng ổn định.")
            return
        lines = [f"• [{a.level.upper()}] {a.title}: {a.message}" for a in alerts]
        self.alert_var.set("\n".join(lines))
        warnings = [a for a in alerts if a.level == "warning"]
        if warnings:
            messagebox.showwarning(
                "Cảnh báo vượt ngưỡng",
                "\n\n".join(f"{a.title}\n{a.message}" for a in warnings),
            )

    # Xử lý sự kiện bấm nút Tính toán (calculate) & Lưu (save)
    # calculate: Tính thử BMI và kiểm tra cảnh báo nhưng không lưu vào database.
    def calculate(self) -> None:
        try:
            values = self._manual_values()
            device = self._device_payload or {}
            bmi, alerts = preview_alerts(
                self.user_id,
                values["weight"],
                values["height"],
                values["activity_minutes"],
                water_ml=values["water_ml"] or int(device.get("water_ml") or 0),
                heart_rate=device.get("heart_rate"),
                sleep_hours=device.get("sleep_hours"),
            )
            status, advice, _ = bmi_recommendation(bmi)
            self.result_var.set(f"BMI: {bmi} — {status}\nGợi ý: {advice}")
            self._show_alerts(alerts)
        except ValueError as exc:
            messagebox.showerror("Dữ liệu không hợp lệ", str(exc))

    def save(self) -> None:
        try:
            payload = self._save_payload()
            source = payload.pop("source")
            log, alerts = create_health_log(self.user_id, **payload, source=source)
            status, advice, _ = bmi_recommendation(log.bmi)
            self.result_var.set(f"Đã lưu hôm nay. BMI: {log.bmi} — {status}\nGợi ý: {advice}")
            self._show_alerts(alerts)
            self.refresh_summary()
            self.on_data_changed()
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Không lưu được", str(exc))

    # Lưu mục tiêu cá nhân (save_goals)
    # save: Gọi create_health_log để lưu chính thức vào DB. 
    # Sau khi lưu xong, cập nhật lại khung tổng quan (refresh_summary()) và phát tín hiệu self.on_data_changed() để các Tab khác (như Biểu đồ) cùng load lại dữ liệu mới.
    # save_goals: Lấy dữ liệu từ 4 ô cài đặt mục tiêu, lưu xuống DB qua hàm
    def save_goals(self) -> None:
        try:
            target_weight_raw = self.target_weight_var.get().strip()
            save_user_goal(
                self.user_id,
                target_weight=float(target_weight_raw) if target_weight_raw else None,
                target_activity=int(self.target_activity_var.get()),
                target_water=int(self.target_water_var.get()),
                max_bmi=float(self.max_bmi_var.get()),
            )
            messagebox.showinfo("Đã lưu", "Mục tiêu cá nhân đã được cập nhật.")
            self.refresh_summary()
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Không lưu mục tiêu", str(exc))

    # Xóa dữ liệu thiết bị (clear_device_data)
    # clear_device_data: Reset toàn bộ dữ liệu cảm biến đồng hồ về gạch ngang (—) và cho _device_payload = None.
    def clear_device_data(self) -> None:
        self._device_payload = None
        self.steps_var.set("—")
        self.heart_var.set("—")
        self.sleep_var.set("—")
        self.device_note_var.set("Đã xóa dữ liệu thiết bị khỏi form. Chỉ còn phần nhập tay.")
        self.result_var.set("Form đã về chế độ nhập tay.")

    # Nhận dữ liệu từ Tab Đồng bộ thiết bị gửi sang (set_device_data)
    # Hàm này được gọi từ bên ngoài (khi người dùng bấm nút "Đồng bộ" bên Tab Thiết bị Giả lập IoT). 
    # Nó tự động đổ dữ liệu cân nặng, chiều cao, bước chân, nhịp tim... vào form này để người dùng xem và lưu lại.
    def set_device_data(
        self,
        weight: float,
        height: float,
        activity: int,
        *,
        steps: int = 0,
        heart_rate: int | None = None,
        sleep_hours: float | None = None,
        water_ml: int = 0,
    ) -> None:
        self.weight_var.set(f"{weight:.1f}")
        self.height_var.set(f"{height:.1f}")
        self.activity_var.set(str(activity))
        if water_ml:
            self.water_var.set(str(water_ml))

        self._device_payload = {
            "steps": steps,
            "heart_rate": heart_rate,
            "sleep_hours": sleep_hours,
            "water_ml": water_ml,
        }
        self.steps_var.set(f"{steps:,}")
        self.heart_var.set("—" if heart_rate is None else str(heart_rate))
        self.sleep_var.set("—" if sleep_hours is None else f"{sleep_hours:.1f}")
        self.device_note_var.set(
            "Đã nhận từ thiết bị giả lập. Bạn có thể sửa cân nặng / vận động rồi bấm Lưu bản ghi."
        )
        self.result_var.set("Dữ liệu thiết bị đã sẵn sàng. Kiểm tra phần nhập tay rồi lưu.")
        try:
            _, alerts = preview_alerts(
                self.user_id,
                weight,
                height,
                activity,
                water_ml=water_ml,
                heart_rate=heart_rate,
                sleep_hours=sleep_hours,
            )
            self._show_alerts(alerts)
        except ValueError:
            pass
