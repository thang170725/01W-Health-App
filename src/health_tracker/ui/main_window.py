"""Main health dashboard window."""

import tkinter as tk
from tkinter import ttk

from .components.ai_tab import AICoachTab
from .components.analytics_tab import AnalyticsTab
from .components.dashboard_tab import DashboardTab
from .components.device_tab import DeviceTab
from .components.history_tab import HistoryTab


class MainWindow(tk.Tk):
    def __init__(self, user_id: int, username: str) -> None:
        super().__init__()
        self.title(f"Personal Health Tracker — {username}")
        self.geometry("920x640")
        self.resizable(False, False)

        header = ttk.Frame(self, padding=(14, 10, 14, 0))
        header.pack(fill="x")
        ttk.Label(header, text="Health Tracker", font=("Segoe UI", 16, "bold")).pack(side="left")
        ttk.Label(header, text=f"Xin chào, {username}", font=("Segoe UI", 10)).pack(side="right")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=12, pady=10)

        self.dashboard = DashboardTab(notebook, user_id, self.refresh_all)
        self.analytics = AnalyticsTab(notebook, user_id)
        self.history = HistoryTab(notebook, user_id, self.refresh_all)
        self.device = DeviceTab(notebook, user_id, self.dashboard.set_device_data)
        self.ai_coach = AICoachTab(notebook, user_id)

        notebook.add(self.dashboard, text="Nhập liệu & Tổng quan")
        notebook.add(self.analytics, text="Biểu đồ")
        notebook.add(self.history, text="Lịch sử")
        notebook.add(self.device, text="Thiết bị giả lập")
        notebook.add(self.ai_coach, text="AI Coach")

        self.refresh_all()

    def refresh_all(self) -> None:
        self.dashboard.refresh_summary()
        self.history.refresh()
        self.analytics.refresh()
