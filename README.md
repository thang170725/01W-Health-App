# Guidelines (hướng dẫn)
```bash
Note: nên sử dụng python 3.10 (Recommanded)

1. Tải repo về máy
    git clone https://github.com/thang170725/01W-Health-App.git
    cd 01W-Health-App

2. Tạo môi trường ảo python
    python3.10 -m venv .venv # hoặc python -m venv .venv (nếu mấy có python version khác)
    .venv\Scripts\activate

3. Tải thư viện
    pip install -r requirements.txt

4. Tạo database tên health_app và tạo bảng (tham khảo trong database/health_app.sql)

5. kết nối database với python (có thể xem video hướng dẫn hoặc chatgpt để làm theo ở bước này)
    tạo .env ở thư mục root (01W-Health-App/.env)
    thêm DB_URL = "mysql+pymysql://thang:123456@localhost:3306/health_app" vào file .env
        - đổi thang -> tên username đã cấu hình trong mysql
        - đổi 123456 -> mật khẩu đã cấu hình trong mysql 

6. test kết nối
    python -m src.config.settings
    nếu log ra như này là kết nối thành công
        # (.venv) thang@PhatToNhuLai:~/workspace/health_app$ python -m src.config.settings
        # mysql+pymysql://thang:123456@localhost:3306/health_app
        # 2026-07-09 09:52:13,073 INFO sqlalchemy.engine.Engine SELECT DATABASE()
        # 2026-07-09 09:52:13,073 INFO sqlalchemy.engine.Engine [raw sql] {}
        # 2026-07-09 09:52:13,074 INFO sqlalchemy.engine.Engine SELECT @@sql_mode
        # 2026-07-09 09:52:13,074 INFO sqlalchemy.engine.Engine [raw sql] {}
        # 2026-07-09 09:52:13,074 INFO sqlalchemy.engine.Engine SELECT @@lower_case_table_names
        # 2026-07-09 09:52:13,074 INFO sqlalchemy.engine.Engine [raw sql] {}
        # DB connected
```