-- ==============================================================================
-- BỘ TRUY VẤN CƠ SỞ DỮ LIỆU ĐẦY ĐỦ 5 NHÓM LỆNH SQL CHO HỆ THỐNG EMS (TMNexora)
-- Dự án: Employee Management System (EMS)
-- Database: MySQL (InnoDB, utf8mb4)
-- Bao gồm đầy đủ: DDL, DML, DQL, DCL, TCL
-- ==============================================================================

USE `ems`;

-- ==============================================================================
-- 1. DDL (DATA DEFINITION LANGUAGE) - ĐỊNH NGHĨA CẤU TRÚC DỮ LIỆU
-- Các lệnh: CREATE, ALTER, DROP, TRUNCATE
-- ==============================================================================

-- 1.1. CREATE DATABASE & CREATE TABLE (Ví dụ tạo bảng phòng ban và nhân viên)
CREATE DATABASE IF NOT EXISTS `ems_backup` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `departments_department_demo` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(150) NOT NULL UNIQUE,
    `code` VARCHAR(20) NOT NULL UNIQUE,
    `description` LONGTEXT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 1.2. ALTER TABLE: Thêm cột, sửa kiểu dữ liệu và tạo ràng buộc khóa ngoại
ALTER TABLE `departments_department_demo` 
    ADD COLUMN `budget` DECIMAL(15, 2) NOT NULL DEFAULT 0.00 AFTER `description`,
    ADD COLUMN `status` VARCHAR(20) NOT NULL DEFAULT 'active';

ALTER TABLE `departments_department_demo`
    MODIFY COLUMN `code` VARCHAR(30) NOT NULL;

-- 1.3. TRUNCATE TABLE: Làm sạch toàn bộ dữ liệu mẫu trong bảng tạm nhưng giữ nguyên cấu trúc
TRUNCATE TABLE `departments_department_demo`;

-- 1.4. DROP TABLE & DROP DATABASE: Xóa cấu trúc khi không còn sử dụng
DROP TABLE IF EXISTS `departments_department_demo`;


-- ==============================================================================
-- 2. DML (DATA MANIPULATION LANGUAGE) - THAO TÁC DỮ LIỆU
-- Các lệnh: INSERT, UPDATE, DELETE
-- ==============================================================================

-- 2.1. INSERT: Thêm hồ sơ phòng ban, chức vụ và nhân sự mới
INSERT INTO `departments_department` (`name`, `code`, `description`, `parent_id`, `manager_id`)
VALUES ('Ban Chuyển Đổi Số', 'DX', 'Nghiên cứu ứng dụng công nghệ số và AI', NULL, NULL);

-- 2.2. UPDATE: Cập nhật điều chỉnh lương cơ bản và người quản lý
UPDATE `employees_employee`
SET `salary` = `salary` * 1.10,
    `updated_at` = NOW()
WHERE `department_id` = (SELECT `id` FROM `departments_department` WHERE `code` = 'KT' LIMIT 1);

-- 2.3. DELETE: Xóa dữ liệu có điều kiện (hoặc Soft Delete theo nghiệp vụ)
DELETE FROM `attendance_attendance`
WHERE `status` = 'pending' AND `date` < '2026-01-01';


-- ==============================================================================
-- 3. DQL (DATA QUERY LANGUAGE) - TRUY VẤN VÀ BÁO CÁO DỮ LIỆU
-- Các mệnh đề: SELECT, WHERE, JOIN, GROUP BY, HAVING, ORDER BY
-- ==============================================================================

-- 3.1. Truy vấn kết hợp JOIN đa bảng: Thông tin nhân viên, phòng ban, chức danh và tài khoản
SELECT 
    e.employee_id,
    CONCAT(u.first_name, ' ', u.last_name) AS full_name,
    u.email,
    u.role,
    d.name AS department_name,
    p.title AS position_title,
    e.salary,
    e.status
FROM `employees_employee` e
INNER JOIN `accounts_user` u ON e.user_id = u.id
LEFT JOIN `departments_department` d ON e.department_id = d.id
LEFT JOIN `departments_position` p ON e.position_id = p.id
WHERE e.status = 'active'
ORDER BY d.name ASC, e.employee_id ASC;

-- 3.2. Truy vấn thống kê tổng hợp (GROUP BY, HAVING, COUNT, SUM, AVG)
-- Thống kê số lượng nhân sự, tổng quỹ lương và lương trung bình theo từng phòng ban
SELECT 
    d.name AS department_name,
    d.code AS department_code,
    COUNT(e.id) AS total_employees,
    SUM(e.salary) AS total_monthly_payroll,
    ROUND(AVG(e.salary), 2) AS average_salary
FROM `departments_department` d
LEFT JOIN `employees_employee` e ON d.id = e.department_id
GROUP BY d.id, d.name, d.code
HAVING total_employees > 0
ORDER BY total_monthly_payroll DESC;


-- ==============================================================================
-- 4. DCL (DATA CONTROL LANGUAGE) - PHÂN QUYỀN TRUY CẬP CƠ SỞ DỮ LIỆU
-- Các lệnh: CREATE USER, GRANT, REVOKE, FLUSH PRIVILEGES
-- ==============================================================================

-- 4.1. Tạo các Database User theo nguyên tắc đặc quyền tối thiểu (Principle of Least Privilege)
-- User 1: Quản trị viên CSDL (DBA)
CREATE USER IF NOT EXISTS 'ems_admin'@'localhost' IDENTIFIED BY 'Admin@Pass2026!';

-- User 2: Ứng dụng Backend Web (Chỉ cần thao tác dữ liệu, không được DROP bảng)
CREATE USER IF NOT EXISTS 'ems_app'@'localhost' IDENTIFIED BY 'WebApp@Pass2026!';

-- User 3: Nhân viên phân tích báo cáo (Chỉ có quyền đọc - Read Only)
CREATE USER IF NOT EXISTS 'ems_readonly'@'localhost' IDENTIFIED BY 'Report@Pass2026!';

-- 4.2. GRANT: Cấp quyền chi tiết theo vai trò
-- Cấp toàn quyền quản trị cho DBA:
GRANT ALL PRIVILEGES ON `ems`.* TO 'ems_admin'@'localhost' WITH GRANT OPTION;

-- Cấp quyền DML + DQL cho Web Application:
GRANT SELECT, INSERT, UPDATE, DELETE ON `ems`.* TO 'ems_app'@'localhost';

-- Cấp quyền chỉ xem (DQL) cho bộ phận báo cáo/audit:
GRANT SELECT ON `ems`.* TO 'ems_readonly'@'localhost';

-- 4.3. REVOKE: Thu hồi quyền nhạy cảm (Không cho ứng dụng thực thi DROP hoặc ALTER)
REVOKE DROP, ALTER, TRUNCATE ON `ems`.* FROM 'ems_app'@'localhost';

-- 4.4. Áp dụng các thay đổi quyền ngay lập tức
FLUSH PRIVILEGES;


-- ==============================================================================
-- 5. TCL (TRANSACTION CONTROL LANGUAGE) - GIAO DỊCH DỮ LIỆU TOÀN VẸN (ACID)
-- Các lệnh: START TRANSACTION, COMMIT, ROLLBACK, SAVEPOINT
-- ==============================================================================

-- Kịch bản nghiệp vụ: Thực hiện chốt bảng lương và giải ngân tháng 10/2026
-- Đảm bảo tính nguyên tử (Atomicity): Hoặc tất cả đều thành công, hoặc không có bản ghi nào bị ghi dở dang

START TRANSACTION;

-- Bước 1: Tạo điểm nhớ (Savepoint) trước khi thao tác
SAVEPOINT before_payroll_update;

-- Bước 2: Cập nhật trạng thái duyệt bảng lương
UPDATE `payroll_payroll`
SET `status` = 'approved',
    `reviewed_by_id` = 1,
    `approved_at` = NOW()
WHERE `month` = 10 AND `year` = 2026 AND `status` = 'calculated';

-- Bước 3: Tạo bản ghi thông báo tự động cho nhân viên
INSERT INTO `notifications_notification` (`title`, `message`, `user_id`, `is_read`, `created_at`)
SELECT 
    'Phiếu lương Tháng 10/2026',
    CONCAT('Bảng lương tháng 10 đã được phê duyệt. Vui lòng kiểm tra phiếu lương chi tiết.'),
    e.user_id,
    0,
    NOW()
FROM `payroll_payroll` p
INNER JOIN `employees_employee` e ON p.employee_id = e.id
WHERE p.month = 10 AND p.year = 2026;

-- Bước 4: Kiểm tra điều kiện logic an toàn:
-- Nếu xảy ra lỗi hoặc phát hiện dữ liệu âm -> ROLLBACK TO SAVEPOINT before_payroll_update;
-- Nếu tất cả hợp lệ -> Xác nhận ghi vĩnh viễn xuống đĩa:
COMMIT;
