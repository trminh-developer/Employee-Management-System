# Employee Management System (EMS)

Hệ thống quản lý nhân sự chuyên nghiệp, được xây dựng dựa trên kiến trúc Django Monolithic kết hợp với FastAPI Microservice cho RESTful API.

## 🚀 Công nghệ sử dụng
- **Backend Core**: Django 5.0 (Python)
- **API Microservice**: FastAPI & Uvicorn
- **Database**: MariaDB / MySQL (thông qua PyMySQL)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript, Chart.js (Dashboard)
- **Bảo mật**: Cơ chế xác thực (Authentication), phân quyền (RBAC: Admin, HR, Employee)

## 📁 Cấu trúc Project
- `apps/`: Chứa các phân hệ nghiệp vụ chính (accounts, attendance, departments, employees, leave, notifications, payroll, performance, reports).
- `config/`: Cấu hình hệ thống (settings, urls, wsgi, asgi).
- `static/`: Tệp tĩnh (CSS, JS, Hình ảnh).
- `templates/`: Giao diện người dùng (Dashboard, Forms, Modals).
- `fastapi_main.py`: Microservice chạy độc lập, cung cấp Real CRUD API.

## ⚙️ Cài đặt và Chạy hệ thống

### 1. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 2. Thiết lập Biến môi trường
Copy file `.env.example` thành `.env` và điền các thông tin kết nối Database của bạn:
```bash
cp .env.example .env
```

### 3. Migrate Database
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Khởi động Server
**Khởi động Django Web Server (Giao diện UI):**
```bash
python manage.py runserver
```
Truy cập: `http://127.0.0.1:8000/`

**Khởi động FastAPI Server (Real CRUD API):**
```bash
python fastapi_main.py
```
Truy cập tài liệu API: `http://127.0.0.1:8001/docs`

## 📊 Tính năng nổi bật
- Dashboard phân tích dữ liệu trực quan bằng biểu đồ.
- Quản lý Hồ sơ, Chấm công, Tính lương và Nghỉ phép.
- Hỗ trợ Popup CRUD Modal mượt mà không cần chuyển trang.
- Đã được tự động hóa bằng Workflow (N8N).
