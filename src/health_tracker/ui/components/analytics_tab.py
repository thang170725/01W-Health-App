"""Weekly / monthly analytics with multiple chart types."""

from __future__ import annotations

import tkinter as tk
from collections import defaultdict
from datetime import date, timedelta
from tkinter import messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ...models.goals_model import get_user_goal
from ...models.health_model import get_logs_in_range


class AnalyticsTab(ttk.Frame):
    # DỰNG THANH CÔNG CỤ VÀ KHUNG VẼ BIỂU ĐỒ (__init__)
    def __init__(self, parent: tk.Misc, user_id: int) -> None:
        # Tạo Frame cho tab báo cáo, lưu user_id và khởi tạo filter_var với giá trị mặc định là "Weekly" (7 ngày).
        super().__init__(parent, padding=10)
        self.user_id = user_id
        self.filter_var = tk.StringVar(value="Weekly")

        # Tạo thanh công cụ (toolbar) chứa ô chọn thời gian (Combobox gồm "Weekly" và "Monthly").
        # filter_box.bind("<<ComboboxSelected>>", ...): Bắt sự kiện khi người dùng đổi từ Weekly $\leftrightarrow$ Monthly thì tự động gọi hàm self.refresh() để vẽ lại biểu đồ.
        # Tạo thêm nút "Làm mới" ở góc phải.
        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew")
        ttk.Label(toolbar, text="Khoảng thời gian").pack(side="left")
        filter_box = ttk.Combobox(
            toolbar,
            textvariable=self.filter_var,
            values=("Weekly", "Monthly"),
            state="readonly",
            width=12,
        )
        filter_box.pack(side="left", padx=(8, 0))
        filter_box.bind("<<ComboboxSelected>>", lambda _event: self.refresh())
        ttk.Button(toolbar, text="Làm mới", command=self.refresh).pack(side="right")

        # self.figure: Khởi tạo đối tượng Figure kích thước $8.6 \times 5.2\text{ inch}$ với độ phân giải $100\text{ DPI}$.
        # FigureCanvasTkAgg: Đóng gói self.figure thành một widget Tkinter và dùng .grid() để đặt vào giao diện.
        self.figure = Figure(figsize=(8.6, 5.2), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

    # HÀM TẢI VÀ VẼ LƯỚI 4 BIỂU ĐỒ (refresh)1. 
    # Lấy dữ liệu và tạo lưới $2 \times 2$
    # days = 7 if ...: Xác định số ngày cần vẽ (7 ngày nếu chọn Weekly, 30 ngày nếu chọn Monthly).
    # self.figure.clear(): Xóa sạch toàn bộ hình vẽ cũ.
    # self.figure.subplots(2, 2): Chia khung vẽ thành 4 ô biểu đồ nằm trên 2 dòng, 2 cột:
    # weight_ax (Dòng 0, Cột 0): Biểu đồ đường Cân nặng.
    # activity_ax (Dòng 0, Cột 1): Biểu đồ cột Vận động.
    # pie_ax (Dòng 1, Cột 0): Biểu đồ tròn/bánh quy Đạt mục tiêu.
    # heat_ax (Dòng 1, Cột 1): Biểu đồ nhiệt (Heatmap) theo ngày trong tuần.
    def refresh(self) -> None:
        try:
            days = 7 if self.filter_var.get() == "Weekly" else 30
            logs = get_logs_in_range(self.user_id, days)
            goal = get_user_goal(self.user_id)
        except RuntimeError as exc:
            messagebox.showerror("Không tải được biểu đồ", str(exc))
            return

        self.figure.clear()
        axes = self.figure.subplots(2, 2)
        weight_ax, activity_ax = axes[0]
        pie_ax, heat_ax = axes[1]

        # Nếu database trả về rỗng, in dòng chữ "Chưa có dữ liệu trong kỳ này" ở chính giữa cả 4 ô và ẩn các trục số.
        if not logs:
            for ax in (weight_ax, activity_ax, pie_ax, heat_ax):
                ax.text(0.5, 0.5, "Chưa có dữ liệu trong kỳ này", ha="center", va="center", transform=ax.transAxes)
                ax.set_xticks([])
                ax.set_yticks([])
            self.figure.tight_layout()
            self.canvas.draw()
            return

        # Biểu đồ 1: Đường xu hướng cân nặng (weight_ax)
        # Vẽ biểu đồ đường (plot) nối các điểm cân nặng theo ngày, có chấm tròn (marker="o"), màu xanh dương.
        # Xoay nhãn ngày $45^\circ$ (labelrotation=45) để các ngày không bị đè lên nhau.4. 
        # Biểu đồ 2: Cột thời gian vận động & Đường mục tiêu (activity_ax)
        labels = [log.log_date.strftime("%d/%m") for log in logs]
        weights = [log.weight for log in logs]
        activities = [log.activity_minutes for log in logs]

        weight_ax.plot(labels, weights, marker="o", color="#187bcd", linewidth=2)
        weight_ax.set_title("Xu hướng cân nặng")
        weight_ax.set_ylabel("kg")
        weight_ax.grid(alpha=0.25)
        weight_ax.tick_params(axis="x", labelrotation=45)

        activity_ax.bar(labels, activities, color="#2a9d6f")
        activity_ax.axhline(goal.target_activity, color="#d62828", linestyle="--", linewidth=1, label="Mục tiêu")
        activity_ax.set_title("Thời gian hoạt động")
        activity_ax.set_ylabel("phút")
        activity_ax.grid(axis="y", alpha=0.25)
        activity_ax.tick_params(axis="x", labelrotation=45)
        activity_ax.legend(loc="upper right", fontsize=8)

        # Biểu đồ 3: Tròn (Donut chart) Tỷ lệ đạt mục tiêu (pie_ax)
        # Tính số ngày Đạt (hit) và Chưa đạt (miss).
        # pie(...): Vẽ biểu đồ tròn. Thuộc tính wedgeprops={"width": 0.45} đục lỗ ở giữa để biến nó thành biểu đồ hình bánh quy (Donut Chart).
        # Màu xanh lá là Đạt, màu vàng là Chưa đạt, kèm tỷ lệ phần trăm (autopct).
        hit = sum(1 for minutes in activities if minutes >= goal.target_activity)
        miss = max(len(activities) - hit, 0)
        pie_ax.pie(
            [hit, miss] if hit + miss else [1],
            labels=["Đạt mục tiêu", "Chưa đạt"] if hit + miss else ["Không có dữ liệu"],
            colors=["#2a9d6f", "#e9c46a"] if hit + miss else ["#cccccc"],
            autopct="%1.0f%%" if hit + miss else None,
            startangle=90,
            wedgeprops={"width": 0.45},
        )
        pie_ax.set_title("Tỷ lệ đạt mục tiêu vận động")

        # Heatmap: weekday (Mon=0) x week index for activity minutes.
        # Biểu đồ 4: Bản đồ nhiệt tần suất tập luyện (heat_ax)
        # Tạo ma trận 2 chiều matrix (Số tuần $\times 7$ ngày trong tuần từ T2 đến CN).
        # Ghi số phút tập luyện vào ô tương ứng trong ma trận.imshow(matrix, cmap="YlGn"): Vẽ Heatmap (màu ô đậm nhạt theo số phút tập). 
        # Màu ô chuyển từ Vàng đến Xanh lá đậm (YlGn).colorbar(...): Thêm thanh chú thích dải màu bên cạnh.
        start = date.today() - timedelta(days=days - 1)
        by_day = defaultdict(int)
        for log in logs:
            by_day[log.log_date] += log.activity_minutes

        weeks = max((days + 6) // 7, 1)
        matrix = [[0.0 for _ in range(7)] for _ in range(weeks)]
        for offset in range(days):
            current = start + timedelta(days=offset)
            week_idx = offset // 7
            weekday = current.weekday()
            matrix[week_idx][weekday] = by_day.get(current, 0)

        image = heat_ax.imshow(matrix, aspect="auto", cmap="YlGn")
        heat_ax.set_title("Heatmap hoạt động (phút)")
        heat_ax.set_xticks(range(7), ["T2", "T3", "T4", "T5", "T6", "T7", "CN"])
        heat_ax.set_yticks(range(weeks), [f"Tuần {i + 1}" for i in range(weeks)])
        self.figure.colorbar(image, ax=heat_ax, fraction=0.046, pad=0.04)

        # BMI category donut as text annotation under pie title if space — already 4 charts.
        # Thống kê phân loại BMI & Render hoàn tất
        # Phân loại các bản ghi vào 4 nhóm BMI (Thiếu cân, Bình thường, Thừa cân, Béo phì).
        # In thêm một dòng chú thích văn bản nhỏ bên dưới biểu đồ tròn.
        # self.figure.tight_layout(): Căn chỉnh lề các biểu đồ tự động để không bị đè chữ.
        # self.canvas.draw(): Vẽ trực tiếp kết quả lên màn hình Tkinter.
        categories = {"Thiếu cân": 0, "Bình thường": 0, "Thừa cân": 0, "Béo phì": 0}
        for log in logs:
            if log.bmi < 18.5:
                categories["Thiếu cân"] += 1
            elif log.bmi < 25:
                categories["Bình thường"] += 1
            elif log.bmi < 30:
                categories["Thừa cân"] += 1
            else:
                categories["Béo phì"] += 1
        # Replace pie with BMI categories when user selects Monthly for variety? Keep activity goal pie;
        # show BMI split as a small legend note on pie_ax.
        pie_ax.text(
            0.5,
            -0.18,
            "BMI: "
            + ", ".join(f"{name} {count}" for name, count in categories.items() if count),
            transform=pie_ax.transAxes,
            ha="center",
            fontsize=8,
        )

        self.figure.tight_layout()
        self.canvas.draw()
