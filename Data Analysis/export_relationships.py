import os
import csv
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

# Query foreign keys from MySQL
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT 
            TABLE_NAME, 
            COLUMN_NAME, 
            CONSTRAINT_NAME, 
            REFERENCED_TABLE_NAME, 
            REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = DATABASE()
          AND REFERENCED_TABLE_NAME IS NOT NULL
        ORDER BY TABLE_NAME, COLUMN_NAME;
    """)
    fk_rows = cursor.fetchall()

# 1. Export CSV
csv_path = r"E:\Project\HeThongQuanLyNhanVien\database_relationships.csv"
with open(csv_path, mode="w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["STT", "Bảng Nguồn (Table)", "Cột Khóa Ngoại (FK)", "Bảng Đích (Referenced Table)", "Cột Khóa Chính (PK)", "Tên Ràng Buộc (Constraint Name)", "Loại Quan Hệ", "Mô Tả Ý Nghĩa"])
    
    stt = 1
    for r in fk_rows:
        tbl, col, cname, ref_tbl, ref_col = r
        rel_type = "1:1" if (tbl == "employees_employee" and col == "user_id") else "1:N"
        
        desc = ""
        if tbl == "employees_employee" and col == "user_id":
            desc = "Liên kết hồ sơ nhân viên với tài khoản đăng nhập người dùng"
        elif tbl == "employees_employee" and col == "department_id":
            desc = "Nhân viên trực thuộc phòng ban nào"
        elif tbl == "employees_employee" and col == "position_id":
            desc = "Chức vụ / vị trí công việc của nhân viên"
        elif tbl == "employees_employee" and col == "manager_id":
            desc = "Quản lý trực tiếp của nhân viên"
        elif tbl == "departments_position" and col == "department_id":
            desc = "Chức vụ thuộc cơ cấu phòng ban nào"
        elif tbl == "departments_department" and col == "manager_id":
            desc = "Trưởng phòng ban (User)"
        elif tbl == "departments_department" and col == "parent_id":
            desc = "Phòng ban cha (cơ cấu cây phân cấp)"
        elif tbl == "attendance_attendance" and col == "employee_id":
            desc = "Dữ liệu chấm công của nhân viên"
        elif tbl == "leave_leaverequest" and col == "employee_id":
            desc = "Đơn xin nghỉ phép của nhân viên"
        elif tbl == "payroll_payroll" and col == "employee_id":
            desc = "Bảng lương chi trả cho nhân viên"
        elif tbl == "performance_performancereview" and col == "employee_id":
            desc = "Nhân viên được đánh giá hiệu suất"
        elif tbl == "performance_performancereview" and col == "reviewer_id":
            desc = "Người thực hiện đánh giá hiệu suất"
        elif tbl == "notifications_notification" and col == "user_id":
            desc = "Thông báo gửi đến người dùng"
        else:
            desc = f"Liên kết hệ thống Django ({cname})"
            
        writer.writerow([stt, tbl, col, ref_tbl, ref_col, cname, rel_type, desc])
        stt += 1

print(f"Exported CSV: {csv_path}")

# 2. Export SQL Constraints
sql_path = r"E:\Project\HeThongQuanLyNhanVien\database_relationships.sql"
with open(sql_path, mode="w", encoding="utf-8") as f:
    f.write("-- ==========================================================\n")
    f.write("-- TỔNG HỢP CÁC RÀNG BUỘC KHÓA NGOẠI (FOREIGN KEYS) HỆ THỐNG EMS\n")
    f.write("-- ==========================================================\n\n")
    for r in fk_rows:
        tbl, col, cname, ref_tbl, ref_col = r
        f.write(f"ALTER TABLE `{tbl}`\n")
        f.write(f"  ADD CONSTRAINT `{cname}`\n")
        f.write(f"  FOREIGN KEY (`{col}`) REFERENCES `{ref_tbl}` (`{ref_col}`)\n")
        f.write("  ON DELETE CASCADE ON UPDATE CASCADE;\n\n")

print(f"Exported SQL: {sql_path}")
