"""Simulated wearable integration tab."""

import random
import tkinter as tk
from tkinter import messagebox, ttk

from ...models.health_model import get_latest_log


class DeviceTab(ttk.Frame):
    def __init__(self, parent: tk.Misc, user_id: int, on_sync) -> None:
        super().__init__(parent, padding=20)
        self.user_id = user_id
        self.on_sync = on_sync
        ttk.Label(self, text="Smart Wearable Simulation", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(self, text="Generate a plausible measurement, then review it in the input tab.").grid(row=1, column=0, sticky="w", pady=(8, 18))
        ttk.Button(self, text="Simulate Sync with Smart Wearable", command=self.sync).grid(row=2, column=0, sticky="w")

    def sync(self) -> None:
        try:
            latest = get_latest_log(self.user_id)
            weight = round((latest.weight if latest else 65.0) + random.uniform(-0.5, 0.5), 1)
            height = latest.height if latest else 170.0
            activity = random.randint(20, 90)
            self.on_sync(weight, height, activity)
            messagebox.showinfo("Device sync complete", "New measurements are ready in the Input & Summary tab.")
        except RuntimeError as exc:
            messagebox.showerror("Could not sync", str(exc))
