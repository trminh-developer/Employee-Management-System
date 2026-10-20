IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'DATABASE_EMS')
BEGIN
    CREATE DATABASE DATABASE_EMS;
END
GO

USE DATABASE_EMS;
GO

-- Xóa bảng cũ nếu đã tồn tại (để chạy lại không bị trùng lặp)
IF OBJECT_ID('NOTIFICATIONS', 'U') IS NOT NULL DROP TABLE NOTIFICATIONS;
IF OBJECT_ID('PERFORMANCE_REVIEWS', 'U') IS NOT NULL DROP TABLE PERFORMANCE_REVIEWS;
IF OBJECT_ID('PAYROLL', 'U') IS NOT NULL DROP TABLE PAYROLL;
IF OBJECT_ID('LEAVE_REQUESTS', 'U') IS NOT NULL DROP TABLE LEAVE_REQUESTS;
IF OBJECT_ID('ATTENDANCE', 'U') IS NOT NULL DROP TABLE ATTENDANCE;
IF OBJECT_ID('EMPLOYEES', 'U') IS NOT NULL DROP TABLE EMPLOYEES;
IF OBJECT_ID('POSITIONS', 'U') IS NOT NULL DROP TABLE POSITIONS;
IF OBJECT_ID('DEPARTMENTS', 'U') IS NOT NULL DROP TABLE DEPARTMENTS;
IF OBJECT_ID('USERS', 'U') IS NOT NULL DROP TABLE USERS;
GO

------------------------------------------------------------------------------------------------------
-- 1. BẢNG TÀI KHOẢN NGƯỜI DÙNG (USERS)
------------------------------------------------------------------------------------------------------
CREATE TABLE USERS (
    UserID INT PRIMARY KEY IDENTITY(1,1),
    Username VARCHAR(50) NOT NULL UNIQUE,
    Password VARCHAR(100) NOT NULL DEFAULT '123456',
    FullName NVARCHAR(100) NOT NULL,
    Email VARCHAR(100) NOT NULL UNIQUE,
    Role NVARCHAR(20) NOT NULL CHECK (Role IN (N'Admin', N'HR', N'Manager', N'Employee')),
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME NOT NULL DEFAULT GETDATE()
)
GO

INSERT INTO USERS (Username, Password, FullName, Email, Role, IsActive)
VALUES
('admin',          '123456', N'Trần Đức Minh',        'admin@ems.com',       N'Admin',    1),
('pct.ngoc',       '123456', N'Nguyễn Bảo Ngọc',      'ngoc.pct@ems.com',    N'Admin',    1),
('loan.marketing', '123456', N'Nguyễn Thị Bích Loan', 'loan.mkt@ems.com',    N'Manager',  1),
('hung.tech',      '123456', N'Trần Quốc Hùng',       'hung.tech@ems.com',   N'Manager',  1),
('hoa.hr',         '123456', N'Phạm Quỳnh Hoa',       'hoa.hr@ems.com',      N'HR',       1),
('tai.fin',        '123456', N'Lê Tấn Tài',           'tai.fin@ems.com',     N'Manager',  1),
('nam.dev',        '123456', N'Đặng Thành Nam',       'nam.dev@ems.com',     N'Employee', 1),
('thao.ui',        '123456', N'Vũ Phương Thảo',       'thao.ui@ems.com',     N'Employee', 1)
GO

SELECT * FROM USERS
GO


------------------------------------------------------------------------------------------------------
-- 2. BẢNG PHÒNG BAN (DEPARTMENTS)
------------------------------------------------------------------------------------------------------
CREATE TABLE DEPARTMENTS (
    DepartmentID INT PRIMARY KEY IDENTITY(1,1),
    DepartmentCode VARCHAR(10) NOT NULL UNIQUE,
    DepartmentName NVARCHAR(100) NOT NULL UNIQUE,
    Description NVARCHAR(255) NULL,
    Budget DECIMAL(15,2) NOT NULL DEFAULT 0.00
)
GO

INSERT INTO DEPARTMENTS (DepartmentCode, DepartmentName, Description, Budget)
VALUES
('BGD', N'Ban Giám Đốc',          N'Hội đồng quản trị và Ban tổng giám đốc',  2000000000.00),
('ENG', N'Engineering',           N'Phòng Kỹ thuật & Phát triển công nghệ',    800000000.00),
('MKT', N'Marketing',             N'Phòng Tiếp thị & Phát triển thương hiệu', 500000000.00),
('HR',  N'Human Resources',       N'Phòng Quản trị Nguồn nhân lực',           300000000.00),
('FIN', N'Finance & Accounting',  N'Phòng Tài chính & Kế toán doanh nghiệp',  400000000.00)
GO

SELECT * FROM DEPARTMENTS
GO


------------------------------------------------------------------------------------------------------
-- 3. BẢNG CHỨC VỤ (POSITIONS)
------------------------------------------------------------------------------------------------------
CREATE TABLE POSITIONS (
    PositionID INT PRIMARY KEY IDENTITY(1,1),
    PositionCode VARCHAR(10) NOT NULL UNIQUE,
    PositionTitle NVARCHAR(100) NOT NULL UNIQUE,
    SalaryCoefficient DECIMAL(4,2) NOT NULL DEFAULT 1.00
)
GO

INSERT INTO POSITIONS (PositionCode, PositionTitle, SalaryCoefficient)
VALUES
('CT',  N'Chủ Tịch HĐQT',    3.00),
('PCT', N'Phó chủ tịch',     2.50),
('GD',  N'Giám đốc',         2.00),
('PGD', N'Phó giám đốc',     1.60),
('TK',  N'Thư ký',           1.20),
('TP',  N'Trưởng phòng',     1.50),
('CV',  N'Chuyên viên',      1.20),
('NV',  N'Nhân viên',        1.00)
GO

SELECT * FROM POSITIONS
GO


------------------------------------------------------------------------------------------------------
-- 4. BẢNG NHÂN VIÊN (EMPLOYEES)
------------------------------------------------------------------------------------------------------
-- Ghi chú: Mã nhân viên (EmployeeCode): Chủ tịch/Phó chủ tịch là số ('0001', '0002')
-- Nhân viên các phòng ban có tiền tố mã ngành ('MKT0001', 'ENG0001'...)
CREATE TABLE EMPLOYEES (
    EmployeeID INT PRIMARY KEY IDENTITY(1,1),
    EmployeeCode VARCHAR(20) NOT NULL UNIQUE,
    FullName NVARCHAR(100) NOT NULL,
    Gender NVARCHAR(10) NOT NULL CHECK (Gender IN (N'Nam', N'Nữ', N'Khác')),
    DateOfBirth DATE NULL,
    PhoneNumber VARCHAR(15) NULL UNIQUE,
    Email VARCHAR(100) NOT NULL UNIQUE,
    Address NVARCHAR(255) NULL,
    DepartmentID INT NOT NULL REFERENCES DEPARTMENTS(DepartmentID),
    PositionID INT NOT NULL REFERENCES POSITIONS(PositionID),
    Salary DECIMAL(15,2) NOT NULL DEFAULT 8000000.00,
    Status NVARCHAR(20) NOT NULL DEFAULT N'Đang làm việc',
    JoinDate DATE NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    UserID INT NULL REFERENCES USERS(UserID)
)
GO

INSERT INTO EMPLOYEES (EmployeeCode, FullName, Gender, DateOfBirth, PhoneNumber, Email, Address, DepartmentID, PositionID, Salary, Status, JoinDate, UserID)
VALUES
('0001',    N'Trần Đức Minh',        N'Nam', '1985-05-15', '0382652732', 'admin@ems.com',    N'Hà Nội',    1, 1, 80000000.00, N'Đang làm việc', '2020-01-01', 1),
('0002',    N'Nguyễn Bảo Ngọc',      N'Nữ',  '1988-09-20', '0912345678', 'ngoc.pct@ems.com', N'Hà Nội',    1, 2, 60000000.00, N'Đang làm việc', '2020-03-01', 2),
('MKT0001', N'Nguyễn Thị Bích Loan', N'Nữ',  '1992-08-14', '0922334455', 'loan.mkt@ems.com', N'TP. HCM',   3, 3, 35000000.00, N'Đang làm việc', '2021-02-15', 3),
('ENG0001', N'Trần Quốc Hùng',       N'Nam', '1990-11-10', '0911223344', 'hung.tech@ems.com',N'Đà Nẵng',   2, 3, 40000000.00, N'Đang làm việc', '2021-04-01', 4),
('HR0001',  N'Phạm Quỳnh Hoa',       N'Nữ',  '1994-02-28', '0988776655', 'hoa.hr@ems.com',   N'Hà Nội',    4, 6, 25000000.00, N'Đang làm việc', '2021-06-10', 5),
('FIN0001', N'Lê Tấn Tài',           N'Nam', '1991-07-07', '0977889900', 'tai.fin@ems.com',  N'Hà Nội',    5, 3, 32000000.00, N'Đang làm việc', '2021-07-01', 6),
('ENG0002', N'Đặng Thành Nam',       N'Nam', '1998-03-12', '0933445566', 'nam.dev@ems.com',  N'Hải Phòng', 2, 8, 18000000.00, N'Đang làm việc', '2022-05-15', 7),
('MKT0002', N'Vũ Phương Thảo',       N'Nữ',  '1999-12-05', '0944556677', 'thao.ui@ems.com',  N'Cần Thơ',   3, 8, 15000000.00, N'Đang làm việc', '2022-08-01', 8)
GO

SELECT * FROM EMPLOYEES
GO


------------------------------------------------------------------------------------------------------
-- 5. BẢNG CHẤM CÔNG (ATTENDANCE)
------------------------------------------------------------------------------------------------------
CREATE TABLE ATTENDANCE (
    AttendanceID BIGINT PRIMARY KEY IDENTITY(1,1),
    EmployeeID INT NOT NULL REFERENCES EMPLOYEES(EmployeeID),
    AttendanceDate DATE NOT NULL,
    CheckIn TIME NULL,
    CheckOut TIME NULL,
    Status NVARCHAR(20) NOT NULL DEFAULT N'Đúng giờ',
    OvertimeHours DECIMAL(4,2) NOT NULL DEFAULT 0.00,
    Note NVARCHAR(255) NULL
)
GO

INSERT INTO ATTENDANCE (EmployeeID, AttendanceDate, CheckIn, CheckOut, Status, OvertimeHours, Note)
VALUES
(1, CAST(GETDATE() AS DATE), '08:00:00', '17:30:00', N'Đúng giờ', 0.5, N'Họp ban lãnh đạo'),
(3, CAST(GETDATE() AS DATE), '08:15:00', '17:30:00', N'Đúng giờ', 0.0, N'Đúng giờ'),
(4, CAST(GETDATE() AS DATE), '08:05:00', '18:30:00', N'Đúng giờ', 1.0, N'Tăng ca dự án core'),
(7, CAST(GETDATE() AS DATE), '08:45:00', '17:30:00', N'Đi muộn',  0.0, N'Kẹt xe đường vành đai')
GO

SELECT * FROM ATTENDANCE
GO


------------------------------------------------------------------------------------------------------
-- 6. BẢNG ĐƠN NGHỈ PHÉP (LEAVE_REQUESTS)
------------------------------------------------------------------------------------------------------
CREATE TABLE LEAVE_REQUESTS (
    RequestID BIGINT PRIMARY KEY IDENTITY(1,1),
    EmployeeID INT NOT NULL REFERENCES EMPLOYEES(EmployeeID),
    LeaveType NVARCHAR(50) NOT NULL DEFAULT N'Nghỉ phép năm',
    StartDate DATE NOT NULL,
    EndDate DATE NOT NULL,
    DurationDays DECIMAL(4,1) NOT NULL DEFAULT 1.0,
    Reason NVARCHAR(500) NULL,
    Status NVARCHAR(20) NOT NULL DEFAULT N'Chờ duyệt' CHECK (Status IN (N'Chờ duyệt', N'Đã duyệt', N'Từ chối')),
    ApprovedBy INT NULL REFERENCES EMPLOYEES(EmployeeID),
    CreatedAt DATETIME NOT NULL DEFAULT GETDATE()
)
GO

INSERT INTO LEAVE_REQUESTS (EmployeeID, LeaveType, StartDate, EndDate, DurationDays, Reason, Status, ApprovedBy)
VALUES
(7, N'Nghỉ phép năm', '2026-10-15', '2026-10-16', 2.0, N'Nghỉ phép thường niên cùng gia đình', N'Đã duyệt',  4),
(8, N'Nghỉ ốm',       '2026-10-20', '2026-10-20', 1.0, N'Đi khám sức khỏe định kỳ',             N'Chờ duyệt', NULL)
GO

SELECT * FROM LEAVE_REQUESTS
GO


------------------------------------------------------------------------------------------------------
-- 7. BẢNG BẢNG LƯƠNG (PAYROLL)
------------------------------------------------------------------------------------------------------
CREATE TABLE PAYROLL (
    PayrollID BIGINT PRIMARY KEY IDENTITY(1,1),
    EmployeeID INT NOT NULL REFERENCES EMPLOYEES(EmployeeID),
    Month INT NOT NULL CHECK (Month BETWEEN 1 AND 12),
    Year INT NOT NULL CHECK (Year >= 2020),
    BaseSalary DECIMAL(15,2) NOT NULL,
    Allowances DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    Bonus DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    OvertimePay DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    Insurance DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    Tax DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    NetSalary AS (BaseSalary + Allowances + Bonus + OvertimePay - Insurance - Tax),
    Status NVARCHAR(20) NOT NULL DEFAULT N'Đã thanh toán',
    PaymentDate DATE NULL
)
GO

INSERT INTO PAYROLL (EmployeeID, Month, Year, BaseSalary, Allowances, Bonus, OvertimePay, Insurance, Tax, Status, PaymentDate)
VALUES
(1, 9, 2026, 80000000.00, 5000000.00, 10000000.00, 0.00, 8400000.00, 3450000.00, N'Đã thanh toán', '2026-10-05'),
(3, 9, 2026, 35000000.00, 2000000.00,  5000000.00, 0.00, 3675000.00, 1200000.00, N'Đã thanh toán', '2026-10-05'),
(4, 9, 2026, 40000000.00, 3000000.00,  5000000.00, 0.00, 4200000.00, 1450000.00, N'Đã thanh toán', '2026-10-05'),
(7, 9, 2026, 18000000.00, 1000000.00,  1000000.00, 0.00, 1890000.00,  350000.00, N'Đã thanh toán', '2026-10-05')
GO

SELECT * FROM PAYROLL
GO


------------------------------------------------------------------------------------------------------
-- 8. BẢNG ĐÁNH GIÁ HIỆU SUẤT (PERFORMANCE_REVIEWS)
------------------------------------------------------------------------------------------------------
CREATE TABLE PERFORMANCE_REVIEWS (
    ReviewID BIGINT PRIMARY KEY IDENTITY(1,1),
    EmployeeID INT NOT NULL REFERENCES EMPLOYEES(EmployeeID),
    ReviewerID INT NOT NULL REFERENCES EMPLOYEES(EmployeeID),
    Period VARCHAR(20) NOT NULL,
    Score DECIMAL(3,1) NOT NULL CHECK (Score BETWEEN 1.0 AND 5.0),
    Feedback NVARCHAR(500) NULL,
    ReviewDate DATE NOT NULL DEFAULT CAST(GETDATE() AS DATE)
)
GO

INSERT INTO PERFORMANCE_REVIEWS (EmployeeID, ReviewerID, Period, Score, Feedback)
VALUES
(7, 4, 'Q3-2026', 4.8, N'Hoàn thành xuất sắc nhiệm vụ và tiến độ dự án core.'),
(8, 3, 'Q3-2026', 4.5, N'Tư duy thiết kế sáng tạo, phối hợp nhịp nhàng với đội nhóm.')
GO

SELECT * FROM PERFORMANCE_REVIEWS
GO


------------------------------------------------------------------------------------------------------
-- 9. BẢNG THÔNG BÁO NỘI BỘ (NOTIFICATIONS)
------------------------------------------------------------------------------------------------------
CREATE TABLE NOTIFICATIONS (
    NotificationID BIGINT PRIMARY KEY IDENTITY(1,1),
    UserID INT NULL REFERENCES USERS(UserID), -- NULL = Toàn công ty
    Title NVARCHAR(200) NOT NULL,
    Content NVARCHAR(MAX) NOT NULL,
    Category NVARCHAR(50) NOT NULL DEFAULT N'Chung',
    Priority NVARCHAR(20) NOT NULL DEFAULT N'Bình thường',
    IsRead BIT NOT NULL DEFAULT 0,
    CreatedAt DATETIME NOT NULL DEFAULT GETDATE()
)
GO

INSERT INTO NOTIFICATIONS (UserID, Title, Content, Category, Priority, IsRead)
VALUES
(NULL, N'Thông báo Lịch nghỉ Lễ', N'Toàn thể công ty nghỉ lễ theo quy định nhà nước.', N'Chính sách', N'Quan trọng', 0),
(7,    N'Phiếu lương Tháng 9/2026', N'Bảng lương tháng 9 của bạn đã được thanh toán.', N'Lương thưởng', N'Bình thường', 1)
GO

SELECT * FROM NOTIFICATIONS
GO


-- ====================================================================================================
-- PHẦN 10: RÀNG BUỘC NGHIỆP VỤ TỰ ĐỘNG (TRIGGERS)
-- ====================================================================================================

-- Trigger 1: Kiểm tra định biên chức vụ phòng ban
-- (Mỗi phòng ban chỉ được phép có tối đa 1 Giám đốc, 1 Phó giám đốc và 1 Thư ký)
IF OBJECT_ID('trg_KiemTraDinhBienPhongBan', 'TR') IS NOT NULL DROP TRIGGER trg_KiemTraDinhBienPhongBan;
GO
CREATE TRIGGER trg_KiemTraDinhBienPhongBan
ON EMPLOYEES
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS (
        SELECT e.DepartmentID, e.PositionID
        FROM EMPLOYEES e
        INNER JOIN POSITIONS p ON e.PositionID = p.PositionID
        WHERE p.PositionTitle IN (N'Giám đốc', N'Phó giám đốc', N'Thư ký')
          AND e.Status = N'Đang làm việc'
        GROUP BY e.DepartmentID, e.PositionID
        HAVING COUNT(*) > 1
    )
    BEGIN
        RAISERROR(N'Lỗi định biên: Mỗi phòng ban chỉ được phép có tối đa 1 Giám đốc, 1 Phó giám đốc và 1 Thư ký!', 16, 1);
        ROLLBACK TRANSACTION;
    END
END
GO

-- Trigger 2: Kiểm tra chuẩn định dạng Mã nhân viên (EmployeeCode)
-- (Chủ tịch/Phó chủ tịch chỉ gồm 4 chữ số '0001'; Nhân viên bắt buộc có mã ngành 'MKT0001', 'ENG0001')
IF OBJECT_ID('trg_KiemTraMaNhanVien', 'TR') IS NOT NULL DROP TRIGGER trg_KiemTraMaNhanVien;
GO
CREATE TRIGGER trg_KiemTraMaNhanVien
ON EMPLOYEES
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    -- Kiểm tra Chủ tịch / Phó chủ tịch (chỉ được phép gồm 4 chữ số)
    IF EXISTS (
        SELECT 1 
        FROM inserted i
        INNER JOIN POSITIONS p ON i.PositionID = p.PositionID
        WHERE p.PositionCode IN ('CT', 'PCT')
          AND i.EmployeeCode NOT LIKE '[0-9][0-9][0-9][0-9]'
    )
    BEGIN
        RAISERROR(N'Mã nhân viên của Chủ tịch hoặc Phó chủ tịch bắt buộc chỉ gồm 4 chữ số (VD: 0001, 0002)!', 16, 1);
        ROLLBACK TRANSACTION;
        RETURN;
    END

    -- Kiểm tra các chức vụ thông thường (bắt buộc phải có chữ in hoa tiền tố + 4 số)
    IF EXISTS (
        SELECT 1 
        FROM inserted i
        INNER JOIN POSITIONS p ON i.PositionID = p.PositionID
        WHERE p.PositionCode NOT IN ('CT', 'PCT')
          AND i.EmployeeCode NOT LIKE '[A-Z]%[0-9][0-9][0-9][0-9]'
    )
    BEGIN
        RAISERROR(N'Mã nhân viên thông thường bắt buộc phải có tiền tố phòng ban và 4 số (VD: MKT0001, ENG0001)!', 16, 1);
        ROLLBACK TRANSACTION;
        RETURN;
    END
END
GO


-- ====================================================================================================
-- PHẦN 11: THỦ TỤC LƯU TRỮ NGHIỆP VỤ (STORED PROCEDURES)
-- ====================================================================================================

-- Thủ tục 1: Thêm nhân viên mới an toàn (Tự động tạo tài khoản USERS và liên kết EMPLOYEES)
IF OBJECT_ID('sp_ThemNhanVien', 'P') IS NOT NULL DROP PROCEDURE sp_ThemNhanVien;
GO
CREATE PROCEDURE sp_ThemNhanVien
    @EmployeeCode   VARCHAR(20),
    @FullName       NVARCHAR(100),
    @Gender         NVARCHAR(10),
    @DateOfBirth    DATE,
    @PhoneNumber    VARCHAR(15),
    @Email          VARCHAR(100),
    @Address        NVARCHAR(255),
    @DepartmentID   INT,
    @PositionID     INT,
    @Salary         DECIMAL(15,2),
    @Username       VARCHAR(50),
    @Password       VARCHAR(100) = '123456'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRANSACTION;
    BEGIN TRY
        -- 1. Thêm tài khoản đăng nhập
        INSERT INTO USERS (Username, Password, FullName, Email, Role, IsActive)
        VALUES (@Username, @Password, @FullName, @Email, N'Employee', 1);

        DECLARE @NewUserID INT = SCOPE_IDENTITY();

        -- 2. Thêm hồ sơ nhân viên
        INSERT INTO EMPLOYEES (EmployeeCode, FullName, Gender, DateOfBirth, PhoneNumber, Email, Address, DepartmentID, PositionID, Salary, UserID)
        VALUES (@EmployeeCode, @FullName, @Gender, @DateOfBirth, @PhoneNumber, @Email, @Address, @DepartmentID, @PositionID, @Salary, @NewUserID);

        COMMIT TRANSACTION;
        PRINT N'==> [sp_ThemNhanVien]: Thêm nhân viên mới thành công: ' + @FullName + N' (' + @EmployeeCode + N')';
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        DECLARE @ErrMsg NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrMsg, 16, 1);
    END CATCH
END
GO

-- Chạy thử nghiệm Thủ tục 1: Thêm nhân viên thử nghiệm
EXEC sp_ThemNhanVien 
    @EmployeeCode = 'ENG0003',
    @FullName     = N'Hoàng Văn Phúc',
    @Gender       = N'Nam',
    @DateOfBirth  = '1997-06-18',
    @PhoneNumber  = '0912998877',
    @Email        = 'phuc.dev@ems.com',
    @Address      = N'Hà Nội',
    @DepartmentID = 2,
    @PositionID   = 8,
    @Salary       = 17000000.00,
    @Username     = 'phuc.dev';
GO

-- Xem lại nhân viên vừa thêm
SELECT * FROM EMPLOYEES WHERE EmployeeCode = 'ENG0003'
GO


-- Thủ tục 2: Tự động tính bảng lương tháng cho toàn bộ nhân viên
IF OBJECT_ID('sp_TinhLuongThang', 'P') IS NOT NULL DROP PROCEDURE sp_TinhLuongThang;
GO
CREATE PROCEDURE sp_TinhLuongThang
    @Month INT,
    @Year  INT
AS
BEGIN
    SET NOCOUNT ON;

    -- Xóa kỳ lương cũ nếu đã tính lại
    DELETE FROM PAYROLL WHERE Month = @Month AND Year = @Year;

    INSERT INTO PAYROLL (EmployeeID, Month, Year, BaseSalary, Allowances, Bonus, OvertimePay, Insurance, Tax, Status, PaymentDate)
    SELECT 
        e.EmployeeID,
        @Month,
        @Year,
        e.Salary AS BaseSalary,
        -- Phụ cấp chức vụ
        CASE 
            WHEN p.PositionCode IN ('CT', 'PCT', 'GD') THEN 5000000.00
            WHEN p.PositionCode IN ('PGD', 'TP')       THEN 3000000.00
            ELSE 1000000.00
        END AS Allowances,
        0.00 AS Bonus,
        -- Tiền tăng ca (150.000đ/giờ)
        ISNULL(SUM(a.OvertimeHours) * 150000.00, 0.00) AS OvertimePay,
        -- Bảo hiểm 10.5% lương cơ bản
        (e.Salary * 0.105) AS Insurance,
        -- Thuế TNCN (5% phần lương vượt trên 11 triệu)
        CASE 
            WHEN e.Salary > 11000000.00 THEN (e.Salary - 11000000.00) * 0.05
            ELSE 0.00
        END AS Tax,
        N'Đã thanh toán',
        GETDATE()
    FROM EMPLOYEES e
    INNER JOIN POSITIONS p ON e.PositionID = p.PositionID
    LEFT JOIN  ATTENDANCE a ON e.EmployeeID = a.EmployeeID AND MONTH(a.AttendanceDate) = @Month AND YEAR(a.AttendanceDate) = @Year
    WHERE e.Status = N'Đang làm việc'
    GROUP BY e.EmployeeID, e.Salary, p.PositionCode;

    PRINT N'==> [sp_TinhLuongThang]: Đã hoàn tất tính bảng lương cho Tháng ' + CAST(@Month AS VARCHAR) + '/' + CAST(@Year AS VARCHAR);
END
GO

-- Chạy thử nghiệm Thủ tục 2: Tính bảng lương tháng 10/2026
EXEC sp_TinhLuongThang @Month = 10, @Year = 2026;
GO

-- Xem lại bảng lương tháng 10 vừa tính
SELECT * FROM PAYROLL WHERE Month = 10 AND Year = 2026
GO


-- Thủ tục 3: Phê duyệt đơn xin nghỉ phép
IF OBJECT_ID('sp_DuyetDonNghiPhep', 'P') IS NOT NULL DROP PROCEDURE sp_DuyetDonNghiPhep;
GO
CREATE PROCEDURE sp_DuyetDonNghiPhep
    @RequestID   BIGINT,
    @Status      NVARCHAR(20),
    @ApprovedBy  INT
AS
BEGIN
    SET NOCOUNT ON;

    IF NOT EXISTS (SELECT 1 FROM LEAVE_REQUESTS WHERE RequestID = @RequestID)
    BEGIN
        RAISERROR(N'Không tìm thấy đơn xin nghỉ phép có ID này!', 16, 1);
        RETURN;
    END

    UPDATE LEAVE_REQUESTS
    SET Status = @Status,
        ApprovedBy = @ApprovedBy
    WHERE RequestID = @RequestID;

    PRINT N'==> [sp_DuyetDonNghiPhep]: Đã duyệt đơn nghỉ phép ID ' + CAST(@RequestID AS VARCHAR) + N' thành: ' + @Status;
END
GO

-- Chạy thử nghiệm Thủ tục 3: Duyệt đơn nghỉ phép ID số 2
EXEC sp_DuyetDonNghiPhep @RequestID = 2, @Status = N'Đã duyệt', @ApprovedBy = 3;
GO

-- Xem lại đơn nghỉ phép vừa duyệt
SELECT * FROM LEAVE_REQUESTS WHERE RequestID = 2
GO


-- ====================================================================================================
-- PHẦN 12: CÁC THAO TÁC DỮ LIỆU: THÊM - SỬA - XÓA (CRUD OPERATIONS: INSERT - UPDATE - DELETE)
-- ====================================================================================================

------------------------------------------------------------------------------------------------------
-- 12.1. CÁC LỆNH THÊM DỮ LIỆU (INSERT INTO)
------------------------------------------------------------------------------------------------------
PRINT N'--------------------------------------------------------------------------------';
PRINT N'==> [12.1] THỰC HIỆN CÁC LỆNH THÊM DỮ LIỆU (INSERT INTO):';
PRINT N'--------------------------------------------------------------------------------';

-- Lệnh 1: Thêm một Phòng ban mới
INSERT INTO DEPARTMENTS (DepartmentCode, DepartmentName, Description, Budget)
VALUES ('IT', N'Phòng Công Nghệ Thông Tin', N'Phụ trách hạ tầng, mạng và an toàn thông tin', 350000000.00);
GO

-- Lệnh 2: Thêm một Chức vụ mới
INSERT INTO POSITIONS (PositionCode, PositionTitle, SalaryCoefficient)
VALUES ('LEAD', N'Trưởng nhóm kỹ thuật (Tech Lead)', 1.80);
GO

-- Lệnh 3: Thêm một Nhân viên mới vào hệ thống
INSERT INTO EMPLOYEES (EmployeeCode, FullName, Gender, DateOfBirth, PhoneNumber, Email, Address, DepartmentID, PositionID, Salary, Status, JoinDate)
VALUES ('ENG0005', N'Lê Hoàng Long', N'Nam', '1996-04-22', '0938887766', 'long.lh@ems.com', N'Số 12 Chùa Bộc, Hà Nội', 2, 8, 19000000.00, N'Đang làm việc', CAST(GETDATE() AS DATE));
GO

-- Lệnh 4: Thêm lượt Chấm công cho nhân viên
INSERT INTO ATTENDANCE (EmployeeID, AttendanceDate, CheckIn, Status, OvertimeHours, Note)
VALUES (2, CAST(GETDATE() AS DATE), '07:55:00', N'Đúng giờ', 1.5, N'Họp chiến dịch Marketing');
GO

-- Lệnh 5: Thêm Đơn xin nghỉ phép
INSERT INTO LEAVE_REQUESTS (EmployeeID, LeaveType, StartDate, EndDate, DurationDays, Reason, Status)
VALUES (5, N'Nghỉ phép năm', '2026-11-01', '2026-11-03', 3.0, N'Về quê thăm gia đình', N'Chờ duyệt');
GO

-- Kiểm tra lại các bản ghi vừa thêm:
SELECT * FROM DEPARTMENTS WHERE DepartmentCode = 'IT';
SELECT * FROM POSITIONS WHERE PositionCode = 'LEAD';
SELECT * FROM EMPLOYEES WHERE EmployeeCode = 'ENG0005';
SELECT * FROM ATTENDANCE WHERE EmployeeID = 2;
SELECT * FROM LEAVE_REQUESTS WHERE EmployeeID = 5;
GO


------------------------------------------------------------------------------------------------------
-- 12.2. CÁC LỆNH SỬA DỮ LIỆU (UPDATE)
------------------------------------------------------------------------------------------------------
PRINT N'--------------------------------------------------------------------------------';
PRINT N'==> [12.2] THỰC HIỆN CÁC LỆNH CẬP NHẬT DỮ LIỆU (UPDATE):';
PRINT N'--------------------------------------------------------------------------------';

-- Lệnh 1: Cập nhật tăng lương 10% cho toàn bộ nhân viên phòng Engineering (DepartmentID = 2)
UPDATE EMPLOYEES
SET Salary = Salary * 1.10
WHERE DepartmentID = 2;
GO

-- Lệnh 2: Cập nhật thay đổi Số điện thoại và Địa chỉ của Chủ tịch HĐQT (EmployeeCode = '0001')
UPDATE EMPLOYEES
SET PhoneNumber = '0988112233',
    Address     = N'Biệt thự Tây Hồ, Hà Nội'
WHERE EmployeeCode = '0001';
GO

-- Lệnh 3: Cập nhật giờ CheckOut và giờ tăng ca trong bảng Chấm công
UPDATE ATTENDANCE
SET CheckOut = '19:30:00',
    OvertimeHours = 2.0,
    Note = N'Tăng ca fix lỗi release hệ thống'
WHERE AttendanceID = 1;
GO

-- Lệnh 4: Cập nhật điều chỉnh Ngân sách hoạt động của phòng Marketing (Tăng thêm 50 triệu)
UPDATE DEPARTMENTS
SET Budget = Budget + 50000000.00
WHERE DepartmentCode = 'MKT';
GO

-- Lệnh 5: Cập nhật trạng thái phê duyệt đơn nghỉ phép
UPDATE LEAVE_REQUESTS
SET Status = N'Đã duyệt',
    ApprovedBy = 1
WHERE RequestID = 1;
GO

-- Kiểm tra lại các bản ghi sau khi cập nhật:
SELECT EmployeeID, EmployeeCode, FullName, Salary, PhoneNumber, Address FROM EMPLOYEES WHERE EmployeeCode IN ('0001', 'ENG0001', 'ENG0002');
SELECT * FROM ATTENDANCE WHERE AttendanceID = 1;
SELECT * FROM DEPARTMENTS WHERE DepartmentCode = 'MKT';
SELECT * FROM LEAVE_REQUESTS WHERE RequestID = 1;
GO


------------------------------------------------------------------------------------------------------
-- 12.3. CÁC LỆNH XÓA DỮ LIỆU (DELETE)
------------------------------------------------------------------------------------------------------
PRINT N'--------------------------------------------------------------------------------';
PRINT N'==> [12.3] THỰC HIỆN CÁC LỆNH XÓA DỮ LIỆU (DELETE):';
PRINT N'--------------------------------------------------------------------------------';

-- Lệnh 1: Xóa một bản ghi chấm công bị ghi sai/trùng lặp (ví dụ AttendanceID = 4)
DELETE FROM ATTENDANCE
WHERE AttendanceID = 4;
GO

-- Lệnh 2: Xóa các thông báo đã đọc cũ trong hệ thống (để dọn dẹp dung lượng)
DELETE FROM NOTIFICATIONS
WHERE IsRead = 1;
GO

-- Lệnh 3: Xóa nhân viên thử nghiệm 'ENG0005' vừa tạo ở bước trên
DELETE FROM EMPLOYEES
WHERE EmployeeCode = 'ENG0005';
GO

-- Lệnh 4: Xóa chức vụ thử nghiệm 'LEAD'
DELETE FROM POSITIONS
WHERE PositionCode = 'LEAD';
GO

-- Lệnh 5: Xóa phòng ban thử nghiệm 'IT'
DELETE FROM DEPARTMENTS
WHERE DepartmentCode = 'IT';
GO

-- Kiểm tra lại sau khi xóa (Các lệnh SELECT này sẽ không còn thấy bản ghi đã xóa):
SELECT * FROM ATTENDANCE WHERE AttendanceID = 4;
SELECT * FROM NOTIFICATIONS;
SELECT * FROM EMPLOYEES WHERE EmployeeCode = 'ENG0005';
SELECT * FROM POSITIONS WHERE PositionCode = 'LEAD';
SELECT * FROM DEPARTMENTS WHERE DepartmentCode = 'IT';
GO


------------------------------------------------------------------------------------------------------
-- 12.4. THỦ TỤC LƯU TRỮ CẬP NHẬT & XÓA NHÂN VIÊN (UPDATE & DELETE STORED PROCEDURES)
------------------------------------------------------------------------------------------------------

-- Thủ tục: Cập nhật thông tin nhân viên (SỬA)
IF OBJECT_ID('sp_CapNhatNhanVien', 'P') IS NOT NULL DROP PROCEDURE sp_CapNhatNhanVien;
GO
CREATE PROCEDURE sp_CapNhatNhanVien
    @EmployeeCode VARCHAR(20),
    @FullName     NVARCHAR(100),
    @PhoneNumber  VARCHAR(15),
    @Address      NVARCHAR(255),
    @Salary       DECIMAL(15,2),
    @Status       NVARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;

    IF NOT EXISTS (SELECT 1 FROM EMPLOYEES WHERE EmployeeCode = @EmployeeCode)
    BEGIN
        RAISERROR(N'Không tìm thấy nhân viên có mã này!', 16, 1);
        RETURN;
    END

    UPDATE EMPLOYEES
    SET FullName    = @FullName,
        PhoneNumber = @PhoneNumber,
        Address     = @Address,
        Salary      = @Salary,
        Status      = @Status
    WHERE EmployeeCode = @EmployeeCode;

    PRINT N'==> [sp_CapNhatNhanVien]: Đã cập nhật thành công nhân viên: ' + @EmployeeCode;
END
GO

-- Chạy thử nghiệm thủ tục CẬP NHẬT:
EXEC sp_CapNhatNhanVien 
    @EmployeeCode = '0001',
    @FullName     = N'Trần Đức Minh (Chủ Tịch)',
    @PhoneNumber  = '0382652732',
    @Address      = N'Hà Nội - Trụ sở chính',
    @Salary       = 85000000.00,
    @Status       = N'Đang làm việc';
GO

-- Xem lại sau khi cập nhật qua Procedure
SELECT EmployeeCode, FullName, PhoneNumber, Address, Salary, Status FROM EMPLOYEES WHERE EmployeeCode = '0001';
GO

-- Thủ tục: Xóa nhân viên (XÓA an toàn - xóa dữ liệu liên quan trước)
IF OBJECT_ID('sp_XoaNhanVien', 'P') IS NOT NULL DROP PROCEDURE sp_XoaNhanVien;
GO
CREATE PROCEDURE sp_XoaNhanVien
    @EmployeeCode VARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRANSACTION;
    BEGIN TRY
        DECLARE @EmpID INT;
        SELECT @EmpID = EmployeeID FROM EMPLOYEES WHERE EmployeeCode = @EmployeeCode;

        IF @EmpID IS NULL
        BEGIN
            RAISERROR(N'Không tìm thấy nhân viên cần xóa!', 16, 1);
            ROLLBACK TRANSACTION;
            RETURN;
        END

        -- 1. Xóa các dữ liệu phụ thuộc của nhân viên
        DELETE FROM ATTENDANCE WHERE EmployeeID = @EmpID;
        DELETE FROM LEAVE_REQUESTS WHERE EmployeeID = @EmpID OR ApprovedBy = @EmpID;
        DELETE FROM PAYROLL WHERE EmployeeID = @EmpID;
        DELETE FROM PERFORMANCE_REVIEWS WHERE EmployeeID = @EmpID OR ReviewerID = @EmpID;

        -- 2. Xóa hồ sơ nhân viên
        DELETE FROM EMPLOYEES WHERE EmployeeID = @EmpID;

        COMMIT TRANSACTION;
        PRINT N'==> [sp_XoaNhanVien]: Đã xóa an toàn nhân viên có mã: ' + @EmployeeCode;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        DECLARE @ErrMsg NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrMsg, 16, 1);
    END CATCH
END
GO

PRINT N'================================================================================';
PRINT N'==> TOÀN BỘ KỊCH BẢN T-SQL (DATABASE_EMS) ĐÃ ĐƯỢC THỰC THI HOÀN TẤT THÀNH CÔNG!';
PRINT N'================================================================================';
GO