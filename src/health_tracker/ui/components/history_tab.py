"""Health record history tab with export."""

from __future__ import annotations

import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ...models.goals_model import get_user_goal
from ...models.health_model import delete_health_log, get_health_logs
from ...models.thresholds import evaluate_alerts


class HistoryTab(ttk.Frame):
    # Khai báo tên các cột hiển thị trên bảng Treeview gồm: Ngày, Cân nặng, Chiều cao, BMI, Vận động, Nước uống, Nguồn dữ liệu (nhập tay hay thiết bị) và Cảnh báo.
    columns = ("date", "weight", "height", "bmi", "activity", "water", "source", "flag")

    # DỰNG BẢNG TREEVIEW VÀ CÁC NÚT BẤM (__init__)
    # Tạo bảng Treeview:
    # show="headings": Chỉ hiện tiêu đề cột, ẩn cột mũi tên phân cấp cây mặc định.
    # selectmode="browse": Người dùng chỉ được bấm chọn một dòng duy nhất tại một thời điểm.
    # height=16: Độ cao hiển thị khoảng 16 dòng.
    def __init__(self, parent: tk.Misc, user_id: int, on_data_changed) -> None:
        super().__init__(parent, padding=12)
        self.user_id = user_id
        self.on_data_changed = on_data_changed

        self.tree = ttk.Treeview(self, columns=self.columns, show="headings", selectmode="browse", height=16)
        labels = (
            "Ngày",
            "Cân (kg)",
            "Cao (cm)",
            "BMI",
            "Vận động",
            "Nước (ml)",
            "Nguồn",
            "Cảnh báo",
        )
        widths = (90, 70, 70, 60, 80, 80, 70, 90)
        for column, label, width in zip(self.columns, labels, widths):
            self.tree.heading(column, text=label)
            self.tree.column(column, width=width, anchor="center")
        # Chạy vòng lặp gán tên tiêu đề tiếng Việt và căn giữa (anchor="center") cùng độ rộng width tương ứng cho từng cột trong bảng.
        # Cấu hình màu nền cho các dòng bằng tag:
        # Thẻ "alert": Đổi nền dòng thành màu hồng đỏ nhạt (#ffe8e8) để highlight dòng có chỉ số vượt ngưỡng.
        # Thẻ "ok": Đổi nền dòng thành màu trắng bình thường.
        self.tree.tag_configure("alert", background="#ffe8e8")
        self.tree.tag_configure("ok", background="#ffffff")

        # Gắn thanh cuộn dọc (Scrollbar) vào cạnh phải của Treeview để cuộn khi danh sách lịch sử quá dài.
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Tạo 2 nút bấm ở phía dưới bảng:
        # Nút "Xuất CSV" nằm bên trái (gọi hàm export_csv).
        # Nút "Xóa bản ghi đã chọn" nằm bên phải (gọi hàm delete_selected).
        # Cho phép bảng tự co dãn khi kéo rộng cửa sổ (rowconfigure / columnconfigure).
        actions = ttk.Frame(self)
        actions.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(actions, text="Xuất CSV", command=self.export_csv).pack(side="left")
        ttk.Button(actions, text="Xóa bản ghi đã chọn", command=self.delete_selected).pack(side="right")

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    # HÀM TẢI & TÔ MÀU DỮ LIỆU LÊN BẢNG (refresh)
    # Xóa sạch dữ liệu cũ đang hiển thị trên bảng trước khi nạp dữ liệu mới.
    # Lấy danh sách bản ghi và mục tiêu cá nhân từ database. Chuẩn bị tập hợp flagged_ids để chứa ID của những bản ghi bị dính cảnh báo.
    def refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            logs = get_health_logs(self.user_id)
            goal = get_user_goal(self.user_id)
            previous = None
            # Insert newest first, but evaluate alerts chronologically.
            chronological = list(logs)
            flagged_ids: set[int] = set()
            # Duyệt dữ liệu theo thứ tự thời gian tăng dần để đánh giá cảnh báo. Nếu có bất kỳ cảnh báo mức nguy hiểm (level == "warning"), lưu id của bản ghi đó vào tập flagged_ids.
            for log in chronological:
                alerts = evaluate_alerts(
                    bmi=log.bmi,
                    weight=log.weight,
                    activity_minutes=log.activity_minutes,
                    water_ml=log.water_ml,
                    heart_rate=log.heart_rate,
                    sleep_hours=log.sleep_hours,
                    previous=previous,
                    goal=goal,
                )
                if any(alert.level == "warning" for alert in alerts):
                    flagged_ids.add(log.id)
                previous = log

            # for log in reversed(chronological): Đảo ngược danh sách để ngày mới nhất lên đầu bảng.
            # Đặt giá trị cột cảnh báo là "Có" nếu ID nằm trong flagged_ids.
            # Đánh nhãn tags=(tag,) ("alert" hoặc "ok") để Treeview tự tô màu hồng đỏ cho dòng bị cảnh báo.
            # Gán id=str(log.id) để lấy ID làm mã định danh cho từng dòng trên giao diện.
            for log in reversed(chronological):
                flag = "Có" if log.id in flagged_ids else ""
                tag = "alert" if log.id in flagged_ids else "ok"
                self.tree.insert(
                    "",
                    "end",
                    iid=str(log.id),
                    values=(
                        log.log_date.isoformat(),
                        f"{log.weight:.1f}",
                        f"{log.height:.1f}",
                        f"{log.bmi:.1f}",
                        log.activity_minutes,
                        log.water_ml,
                        log.source,
                        flag,
                    ),
                    tags=(tag,),
                )
        except RuntimeError as exc:
            messagebox.showerror("Không tải được lịch sử", str(exc))

    # HÀM XÓA BẢN GHI ĐÃ CHỌN (delete_selected)
    # self.tree.selection(): Lấy ID dòng người dùng đang con trỏ chọn trên bảng.
    # Nếu chưa chọn dòng nào, hiện popup nhắc nhở.
    # Nếu có chọn, hiện hộp thoại xác nhận askyesno (Có / Không).
    def delete_selected(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Chọn bản ghi", "Hãy chọn một dòng trước.")
            return
        if not messagebox.askyesno("Xóa bản ghi", "Xóa bản ghi sức khỏe đã chọn?"):
            return
        
        # Gọi delete_health_log để xóa bản ghi tương ứng khỏi DB.
        # Gọi callback self.on_data_changed() để kích hoạt tải lại dữ liệu đồng bộ trên tất cả các tab khác.
        try:
            delete_health_log(self.user_id, int(selected[0]))
            self.on_data_changed()
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Không xóa được", str(exc))

    # HÀM XUẤT FILE CSV (export_csv)
    # Bật hộp thoại hệ thống asksaveasfilename cho phép người dùng chọn thư mục và đặt tên file xuất (mặc định đuôi .csv). Nếu người dùng bấm "Hủy" (Cancel), path sẽ rỗng và thoát hàm.
    def export_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Xuất lịch sử sức khỏe",
            defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            logs = get_health_logs(self.user_id)
            # Lấy toàn bộ lịch sử ghi nhận của người dùng. Mở đường dẫn file với chuẩn mã hóa chữ utf-8 và tạo đối tượng csv.writer, sau đó ghi dòng tiêu đề cột (Header) đầu tiên vào file.
            with open(path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(
                    [
                        "date",
                        "weight",
                        "height",
                        "bmi",
                        "activity_minutes",
                        "steps",
                        "heart_rate",
                        "sleep_hours",
                        "water_ml",
                        "source",
                    ]
                )
                
                # Dùng vòng lặp ghi từng bản ghi dữ liệu thành từng dòng trong file CSV (bao gồm cả các chỉ số đo từ thiết bị IoT như steps, heart_rate, sleep_hours).
                # Bật thông báo messagebox.showinfo báo xuất file thành công kèm đường dẫn tới file vừa lưu.
                for log in logs:
                    writer.writerow(
                        [
                            log.log_date.isoformat(),
                            log.weight,
                            log.height,
                            log.bmi,
                            log.activity_minutes,
                            log.steps,
                            log.heart_rate,
                            log.sleep_hours,
                            log.water_ml,
                            log.source,
                        ]
                    )
            messagebox.showinfo("Xuất thành công", f"Đã lưu file:\n{path}")
        except (OSError, RuntimeError) as exc:
            messagebox.showerror("Không xuất được", str(exc))
