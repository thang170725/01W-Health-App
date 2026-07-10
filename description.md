Act as a Senior Python Developer expert in Tkinter and SQLAlchemy (ORM). I need you to generate a Personal Health Tracking Application (App Theo dõi Sức khỏe Cá nhân) with standard, modular architecture. 

Ensure the code is robust, handles exceptions via SQLAlchemy sessions, includes clear comments, and works out-of-the-box.

### 1. PROJECT ARCHITECTURE & FILE STRUCTURE
Create the project following this modular structure to separate UI, Logic, and Database layers:
health_tracker/
│
├── config.py             # Database connection & URL settings (using SQLAlchemy)
├── database.py           # Engine initialization, Base model declaration, and session helper
├── main.py               # Application entry point (Initializes DB and runs LoginWindow)
│
├── models/
│   ├── __init__.py
│   ├── db_models.py      # SQLAlchemy ORM classes (User, HealthLog)
│   ├── auth_model.py     # Login/Register business logic using SQLAlchemy sessions
│   └── health_model.py   # Health data CRUD, BMI logic, history query logic
│
└── ui/
    ├── __init__.py
    ├── main_window.py    # Main dashboard with tabs/views
    ├── login_window.py   # Login & Registration screens
    └── components/       # Custom reusable UI elements (charts, forms)
        ├── __init__.py
        ├── dashboard_tab.py
        ├── history_tab.py
        └── device_tab.py

### 2. DATABASE SCHEMA WITH SQLALCHEMY ORM
Inside `models/db_models.py`, define the schema using SQLAlchemy's declarative base:
- **User Model (`User` class)**: 
  - `id`: Integer, primary_key=True
  - `username`: String(50), unique=True, nullable=False
  - `password`: String(100), nullable=False (store plain text for simplicity or hashed)
  - `age`: Integer
  - `gender`: String(10)
  - Relationship to `HealthLog` (backref='user', cascade='all, delete-orphan')
- **HealthLog Model (`HealthLog` class)**:
  - `id`: Integer, primary_key=True
  - `user_id`: Integer, ForeignKey('users.id'), nullable=False
  - `log_date`: Date, nullable=False
  - `weight`: Float, nullable=False
  - `height`: Float, nullable=False
  - `bmi`: Float, nullable=False
  - `activity_minutes`: Integer, default=0

In `database.py`, use `Base.metadata.create_all(engine)` to automatically bootstrap tables upon application startup.

### 3. USER FLOW & UI REQUIREMENTS
- **Style:** Clean, user-friendly, and neat Tkinter interface using standard widgets or `tkinter.ttk`. Use reasonable padding and grid alignment.
- **Flow:**
  1. Run `main.py` -> Show `LoginWindow`.
  2. `LoginWindow` provides Login or Toggle to Register view.
  3. On successful validation, close `LoginWindow` and boot `MainWindow` (Dashboard), passing the logged-in `user_id` as the session state.

### 4. CORE FUNCTIONALITIES TO IMPLEMENT
Implement these features inside `MainWindow` via a `ttk.Notebook` layout:

#### Tab 1: Input & Summary (Nhập liệu & Tổng quan)
- Input form: Weight (kg), Height (cm), Sports/Activity duration (minutes).
- **BMI Calculator:** Automatically compute BMI ($BMI = \frac{weight}{(height/100)^2}$) upon click. Display instant WHO health recommendations:
  - < 18.5: Underweight (Gợi ý: Tăng cường dinh dưỡng).
  - 18.5 - 24.9: Normal (Gợi ý: Duy trì phong độ tốt).
  - 25 - 29.9: Overweight (Gợi ý: Kiểm soát chế độ ăn, tăng cường vận động).
  - >= 30: Obese (Cảnh báo: Nguy cơ béo phì, cần tư vấn y tế).
- **Threshold Alerts:** Show a `tkinter.messagebox.showwarning` if BMI hits Overweight/Obese status.

#### Tab 2: Analytics & Charts (Biểu đồ & Theo dõi)
- Embed charts into the Tkinter tab frame using `matplotlib.backends.backend_tkagg`.
- Provide a dropdown option to select filter mode: **Weekly (Theo tuần)** and **Monthly (Theo tháng)**.
- Render a line plot for Weight trends and a bar chart for Activity minutes using data queried from SQLAlchemy.

#### Tab 3: History Log (Lịch sử & Nhật ký)
- A `ttk.Treeview` component displaying all previous health logs linked to the current `user_id`.
- Include a "Delete entry" button that deletes the selected record from the database using SQLAlchemy session.

#### Tab 4: Smart Wearable Simulation (Giả lập Đồng bộ)
- A button named "Simulate Sync with Smart Wearable" (Đồng bộ thiết bị).
- When clicked, use Python's `random` to mock external device data: generates slightly variable weight (e.g., +/- 0.5kg variance from the last entry if available) and sports minutes (range 20 to 90). 
- Insert these mocked values straight into Tab 1's input fields for the user to double-check and save.

### 5. EXECUTION REQUIREMENTS
- Write the full code structure step-by-step. Do not cut corners or use `# TODO`.
- Manage SQLAlchemy sessions cleanly using context managers or proper session close calls (`session.close()`) in `try-except-finally` blocks to prevent locked instances.

Let's begin file-by-file starting with `config.py`, `database.py`, and `models/db_models.py`.