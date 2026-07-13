"""Input and summary tab."""

import tkinter as tk
from tkinter import messagebox, ttk

from ...models.health_model import bmi_recommendation, calculate_bmi, create_health_log


class DashboardTab(ttk.Frame):
    def __init__(self, parent: tk.Misc, user_id: int, on_data_changed) -> None:
        super().__init__(parent, padding=20)
        self.user_id = user_id
        self.on_data_changed = on_data_changed
        self.weight_var = tk.StringVar()
        self.height_var = tk.StringVar()
        self.activity_var = tk.StringVar(value="0")
        self.result_var = tk.StringVar(value="Enter your data to calculate BMI.")
        self._build()

    def _build(self) -> None:
        form = ttk.LabelFrame(self, text="Daily health record", padding=16)
        form.grid(row=0, column=0, sticky="new")
        self.columnconfigure(0, weight=1)
        fields = (("Weight (kg)", self.weight_var), ("Height (cm)", self.height_var), ("Activity (minutes)", self.activity_var))
        for row, (label, variable) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)
            ttk.Entry(form, textvariable=variable, width=24).grid(row=row, column=1, sticky="ew", pady=6)
        ttk.Button(form, text="Calculate BMI", command=self.calculate).grid(row=3, column=0, pady=(14, 0), sticky="w")
        ttk.Button(form, text="Save record", command=self.save).grid(row=3, column=1, pady=(14, 0), sticky="e")
        ttk.Label(self, textvariable=self.result_var, wraplength=540, justify="left").grid(
            row=1, column=0, sticky="w", pady=(20, 0)
        )

    def _values(self) -> tuple[float, float, int]:
        try:
            return float(self.weight_var.get()), float(self.height_var.get()), int(self.activity_var.get())
        except ValueError as exc:
            raise ValueError("Weight, height, and activity must be valid numbers.") from exc

    def calculate(self) -> float | None:
        try:
            weight, height, _ = self._values()
            bmi = calculate_bmi(weight, height)
            status, advice, should_warn = bmi_recommendation(bmi)
            self.result_var.set(f"BMI: {bmi} - {status}\nRecommendation: {advice}")
            if should_warn:
                messagebox.showwarning("BMI warning", f"BMI {bmi}: {status}.\n{advice}")
            return bmi
        except ValueError as exc:
            messagebox.showerror("Invalid data", str(exc))
            return None

    def save(self) -> None:
        try:
            weight, height, activity = self._values()
            log = create_health_log(self.user_id, weight, height, activity)
            status, advice, should_warn = bmi_recommendation(log.bmi)
            self.result_var.set(f"Saved today. BMI: {log.bmi} - {status}\nRecommendation: {advice}")
            if should_warn:
                messagebox.showwarning("BMI warning", f"BMI {log.bmi}: {status}.\n{advice}")
            self.on_data_changed()
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Could not save", str(exc))

    def set_device_data(self, weight: float, height: float, activity: int) -> None:
        self.weight_var.set(f"{weight:.1f}")
        self.height_var.set(f"{height:.1f}")
        self.activity_var.set(str(activity))
        self.result_var.set("Device data was added. Please review it, then save the record.")
