"""AI health coach tab powered by Gemini."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from ...services.ai_coach import generate_health_advice


class AICoachTab(ttk.Frame):
    def __init__(self, parent: tk.Misc, user_id: int) -> None:
        super().__init__(parent, padding=14)
        self.user_id = user_id
        self._busy = False

        ttk.Label(self, text="AI Coach — gợi ý sức khỏe", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            self,
            text="Dựa trên hồ sơ và nhật ký gần đây, AI gợi ý nên ăn gì, uống gì và tập gì. Không thay thế tư vấn y tế.",
            wraplength=780,
        ).grid(row=1, column=0, sticky="w", pady=(6, 10))

        actions = ttk.Frame(self)
        actions.grid(row=2, column=0, sticky="ew")
        self.generate_btn = ttk.Button(actions, text="Tạo gợi ý hôm nay", command=self.generate)
        self.generate_btn.pack(side="left")
        self.status_var = tk.StringVar(value="Sẵn sàng.")
        ttk.Label(actions, textvariable=self.status_var).pack(side="left", padx=(12, 0))

        self.output = scrolledtext.ScrolledText(self, wrap="word", height=22, width=96, font=("Segoe UI", 10))
        self.output.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        self.output.insert("1.0", "Nhấn “Tạo gợi ý hôm nay” để nhận lời khuyên từ Gemini (hoặc gợi ý offline nếu API lỗi).")
        self.output.configure(state="disabled")

        self.rowconfigure(3, weight=1)
        self.columnconfigure(0, weight=1)

    def generate(self) -> None:
        if self._busy:
            return
        self._busy = True
        self.generate_btn.configure(state="disabled")
        self.status_var.set("Đang tạo gợi ý...")

        def worker() -> None:
            try:
                advice = generate_health_advice(self.user_id)
                self.after(0, lambda: self._show_result(advice, None))
            except Exception as exc:  # noqa: BLE001
                self.after(0, lambda: self._show_result(None, str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _show_result(self, advice: str | None, error: str | None) -> None:
        self._busy = False
        self.generate_btn.configure(state="normal")
        if error:
            self.status_var.set("Thất bại.")
            messagebox.showerror("AI Coach", error)
            return
        self.status_var.set("Hoàn tất.")
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", advice or "")
        self.output.configure(state="disabled")
