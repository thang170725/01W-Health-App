"""Main health dashboard window."""

import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ..models.health_model import get_health_logs
from .components.dashboard_tab import DashboardTab
from .components.device_tab import DeviceTab
from .components.history_tab import HistoryTab


class AnalyticsTab(ttk.Frame):
    def __init__(self, parent: tk.Misc, user_id: int) -> None:
        super().__init__(parent, padding=14)
        self.user_id = user_id
        self.filter_var = tk.StringVar(value="Weekly")
        ttk.Label(self, text="View").grid(row=0, column=0, sticky="w")
        filter_box = ttk.Combobox(self, textvariable=self.filter_var, values=("Weekly", "Monthly"), state="readonly", width=12)
        filter_box.grid(row=0, column=1, sticky="w", padx=(8, 0))
        filter_box.bind("<<ComboboxSelected>>", lambda _event: self.refresh())
        self.figure = Figure(figsize=(7.4, 4.4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
        self.rowconfigure(1, weight=1)
        self.columnconfigure(1, weight=1)

    def refresh(self) -> None:
        try:
            logs = get_health_logs(self.user_id)
        except RuntimeError as exc:
            messagebox.showerror("Could not load analytics", str(exc))
            return
        cutoff = date.today() - timedelta(days=6 if self.filter_var.get() == "Weekly" else 29)
        logs = [log for log in logs if log.log_date >= cutoff]
        self.figure.clear()
        weight_ax, activity_ax = self.figure.subplots(2, 1)
        if logs:
            labels = [log.log_date.strftime("%d/%m") for log in logs]
            weight_ax.plot(labels, [log.weight for log in logs], marker="o", color="#187bcd")
            activity_ax.bar(labels, [log.activity_minutes for log in logs], color="#2a9d6f")
        else:
            weight_ax.text(0.5, 0.5, "No health records in this period", ha="center", va="center", transform=weight_ax.transAxes)
        weight_ax.set_title("Weight trend")
        weight_ax.set_ylabel("kg")
        weight_ax.grid(alpha=0.25)
        activity_ax.set_title("Activity duration")
        activity_ax.set_ylabel("minutes")
        activity_ax.grid(axis="y", alpha=0.25)
        self.figure.tight_layout()
        self.canvas.draw()


class MainWindow(tk.Tk):
    def __init__(self, user_id: int, username: str) -> None:
        super().__init__()
        self.title(f"Personal Health Tracker - {username}")
        self.geometry("820x620")
        self.minsize(720, 520)
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)
        self.dashboard = DashboardTab(notebook, user_id, self.refresh_all)
        self.analytics = AnalyticsTab(notebook, user_id)
        self.history = HistoryTab(notebook, user_id, self.refresh_all)
        self.device = DeviceTab(notebook, user_id, self.dashboard.set_device_data)
        notebook.add(self.dashboard, text="Input & Summary")
        notebook.add(self.analytics, text="Analytics & Charts")
        notebook.add(self.history, text="History Log")
        notebook.add(self.device, text="Smart Wearable")
        self.refresh_all()

    def refresh_all(self) -> None:
        self.history.refresh()
        self.analytics.refresh()
