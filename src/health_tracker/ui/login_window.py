"""Login and registration window."""

import tkinter as tk
from tkinter import messagebox, ttk

from ..models.auth_model import authenticate, register_user


class LoginWindow(tk.Tk):
    def __init__(self, on_login) -> None:
        super().__init__()                      # gọi contructer của tk.Tk (nếu không có dòng này tk sẽ không tạo cửa sổ)

        self.on_login = on_login                # lưu callback
        self.is_register_mode = False           # False là đang ở đăng nhập, True là chuyển đến đăng ký

        self.title("Personal Health Tracker")
        self.geometry("390x360")
        self.resizable(False, False)

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.age_var = tk.StringVar()
        self.gender_var = tk.StringVar()

        self.form = ttk.Frame(self, padding=28)
        self.form.pack(fill="both", expand=True)

        self.render()

    def render(self) -> None:
        for widget in self.form.winfo_children():
            widget.destroy()

        title = "Create account" if self.is_register_mode else "Sign in"
        ttk.Label(self.form, text=title, font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 18))
        self._entry(1, "Username", self.username_var)
        self._entry(2, "Password", self.password_var, show="*")

        if self.is_register_mode:
            self._entry(3, "Age (optional)", self.age_var)
            ttk.Label(self.form, text="Gender (optional)").grid(row=4, column=0, sticky="w", pady=6)
            ttk.Combobox(self.form, textvariable=self.gender_var, values=("Male", "Female", "Other"), state="readonly", width=23).grid(row=4, column=1, pady=6)
            
        action_row = 5 if self.is_register_mode else 3
        ttk.Button(self.form, text=title, command=self.submit).grid(row=action_row, column=0, columnspan=2, sticky="ew", pady=(16, 8))
        toggle = "Already have an account? Sign in" if self.is_register_mode else "New user? Register"
        ttk.Button(self.form, text=toggle, command=self.toggle).grid(row=action_row + 1, column=0, columnspan=2)
        self.form.columnconfigure(1, weight=1)

    def _entry(self, row: int, label: str, variable: tk.StringVar, show: str | None = None) -> None:
        ttk.Label(self.form, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)
        ttk.Entry(self.form, textvariable=variable, show=show or "").grid(row=row, column=1, sticky="ew", pady=6)

    def toggle(self) -> None:
        self.is_register_mode = not self.is_register_mode
        self.render()

    def submit(self) -> None:
        try:
            if self.is_register_mode:
                age = int(self.age_var.get()) if self.age_var.get().strip() else None
                if age is not None and age <= 0:
                    raise ValueError("Age must be greater than zero.")
                user = register_user(self.username_var.get(), self.password_var.get(), age, self.gender_var.get())
                messagebox.showinfo("Account created", "Registration successful. You are now signed in.")
            else:
                user = authenticate(self.username_var.get(), self.password_var.get())
                if not user:
                    messagebox.showerror("Sign in failed", "Incorrect username or password.")
                    return
            self.destroy()
            self.on_login(user.id, user.username)
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Could not continue", str(exc))
