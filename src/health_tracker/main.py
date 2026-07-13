"""Application entry point. Run with: python -m src.health_tracker.main"""

from .database import initialize_database
from .ui.login_window import LoginWindow
from .ui.main_window import MainWindow


def launch_dashboard(user_id: int, username: str) -> None:
    dashboard = MainWindow(user_id, username)
    dashboard.mainloop()


def main() -> None:
    initialize_database()
    login = LoginWindow(launch_dashboard)
    login.mainloop()


if __name__ == "__main__":
    main()
