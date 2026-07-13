"""Health record history tab."""

import tkinter as tk
from tkinter import messagebox, ttk

from ...models.health_model import delete_health_log, get_health_logs


class HistoryTab(ttk.Frame):
    columns = ("date", "weight", "height", "bmi", "activity")

    def __init__(self, parent: tk.Misc, user_id: int, on_data_changed) -> None:
        super().__init__(parent, padding=14)
        self.user_id = user_id
        self.on_data_changed = on_data_changed
        self.tree = ttk.Treeview(self, columns=self.columns, show="headings", selectmode="browse")
        labels = ("Date", "Weight (kg)", "Height (cm)", "BMI", "Activity (min)")
        for column, label in zip(self.columns, labels):
            self.tree.heading(column, text=label)
            self.tree.column(column, width=120, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        ttk.Button(self, text="Delete selected entry", command=self.delete_selected).grid(row=1, column=0, sticky="e", pady=(12, 0))
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            for log in reversed(get_health_logs(self.user_id)):
                self.tree.insert("", "end", iid=str(log.id), values=(
                    log.log_date.isoformat(), f"{log.weight:.1f}", f"{log.height:.1f}",
                    f"{log.bmi:.1f}", log.activity_minutes,
                ))
        except RuntimeError as exc:
            messagebox.showerror("Could not load history", str(exc))

    def delete_selected(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select a record", "Choose a health record first.")
            return
        if not messagebox.askyesno("Delete record", "Delete the selected health record?"):
            return
        try:
            delete_health_log(self.user_id, int(selected[0]))
            self.on_data_changed()
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Could not delete", str(exc))
