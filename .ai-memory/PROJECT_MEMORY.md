# 📚 PROJECT MEMORY

## 1. Thông tin chung
- **Tên dự án:** Hệ Thống Quản Lý Nhân Viên (Enterprise HR System)
- **Mục tiêu:** Quản lý hồ sơ nhân sự, phòng ban, lương, phép, điểm danh và phân quyền RBAC.
- **Tech Stack:**
  - Backend: Django 5, FastAPI (Microservice chạy song song kết nối Django ORM)
  - Frontend: HTML/CSS/JS (Vanilla, Bootstrap), Chart.js, SheetJS
  - Database: MySQL (XAMPP)

## 2. Quy tắc Coding (Coding Conventions)
- **FastAPI:** Sử dụng `@sync_to_async` khi gọi Django ORM. Dùng `HTTPBearer` cho phân quyền. Trả về format chuẩn `{"status", "message", "data"}` hoặc theo Schema.
- **Django:** Logic chia theo Apps (`accounts`, `employees`, `payroll`, v.v.).

## 3. Cấu trúc thư mục cốt lõi
- `apps/`: Các module nghiệp vụ (employees, payroll, departments...)
- `config/`: Cấu hình hệ thống Django
- `templates/`: Giao diện HTML (Render bằng Django)
- `static/`: Chứa file CSS, JS
- `fastapi_main.py`: File chạy API bằng uvicorn.

## 4. Tình trạng hiện tại
- **Giai đoạn:** Đang phát triển / Hoàn thiện RBAC và UI Reports.
- **Lỗi đã biết (Known Issues):** FastAPI bị timeout connection -> Đã sửa bằng middleware `close_old_connections`.
