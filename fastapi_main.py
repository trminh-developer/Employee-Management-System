import os
import sys
from asgiref.sync import sync_to_async

# --- Cấu hình tích hợp Django ORM vào FastAPI ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
try:
    import django
    django.setup()
except Exception as e:
    print("Vui lòng chạy script này từ thư mục gốc của dự án Django.")
    sys.exit(1)

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any
from datetime import datetime, timedelta, timezone
import jwt

from django.db import close_old_connections
from django.contrib.auth import authenticate
from apps.employees.models import Employee
from apps.accounts.models import User
from fastapi.responses import RedirectResponse

# Khởi tạo FastAPI App
app = FastAPI(
    title="Enterprise HR API", 
    description="Hệ thống API Quản lý Nhân sự với RBAC (Role-Based Access Control)", 
    version="2.0.0"
)

@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/docs")

# Middleware tự động dọn dẹp kết nối Database cũ/chết của Django & gắn Correlation ID (X-Request-ID)
@app.middleware("http")
async def db_session_middleware(request, call_next):
    import uuid
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    close_old_connections()
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        close_old_connections()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- JWT Config ---
SECRET_KEY = "super_secret_jwt_key_for_fastapi_123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Dùng HTTPBearer thay vì OAuth2 để Swagger UI hiển thị form nhập Token cực gọn (Không bị thừa client_id, scope...)
security_scheme = HTTPBearer()

def create_access_token(user: dict):
    """
    Format Access Token Payload chứa đầy đủ thông tin định danh và phân quyền.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user["username"],
        "user_id": user["id"],
        "role": user["role"],
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user: dict):
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user["username"],
        "type": "refresh",
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    username: str = Field(default="admin", examples=["admin"], description="Tên đăng nhập hoặc Email (@ems.com)")
    password: str = Field(default="123456", examples=["123456"], description="Mật khẩu (mặc định: 123456)")

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class EmployeeOut(BaseModel):
    id: int
    employee_id: str
    first_name: str
    last_name: str
    email: str
    department: Optional[str] = None
    position: Optional[str] = None
    phone: str
    status: str

class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    phone: str
    status: str = "active"

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[str] = None

# --- Helper Functions (Sync to Async) ---
@sync_to_async
def authenticate_user_db(username: str, password: str):
    user: Any = authenticate(username=username, password=password)
    if user is None and "@" in username:
        matched_user = User.objects.filter(email=username, is_active=True).first()
        if matched_user:
            user = authenticate(username=matched_user.username, password=password)
    if user is not None and getattr(user, 'is_active', False):
        user_id = getattr(user, 'id', None)
        emp = Employee.objects.filter(user_id=user_id).first()
        if emp and emp.status == 'inactive':
            return None
        return {"id": user_id, "username": getattr(user, 'username', ''), "role": getattr(user, 'role', 'employee')}
    return None

@sync_to_async
def get_user_by_username(username: str):
    try:
        user = User.objects.get(username=username, is_active=True)
        emp = Employee.objects.filter(user_id=user.id).first()
        if emp and emp.status == 'inactive':
            return None
        return {"id": user.id, "username": user.username, "role": user.role}
    except User.DoesNotExist:
        return None

@sync_to_async
def get_employees_db(skip: int, limit: int, user_role: str, user_id: int, include_inactive: bool = False):
    from django.db.models import Q
    # RBAC Data Filtering + Deterministic Ordering:
    # Mặc định không trả về nhân sự đang ở trạng thái 'inactive' (Đã khóa / Ngưng hoạt động)
    qs = Employee.objects.select_related('user', 'department', 'position').order_by('id')
    if not include_inactive:
        qs = qs.exclude(status='inactive').filter(user__is_active=True)
    
    if user_role == 'employee':
        qs = qs.filter(user_id=user_id)
    elif user_role == 'manager':
        mgr_emp = Employee.objects.filter(user_id=user_id).first()
        if mgr_emp and mgr_emp.department_id:
            qs = qs.filter(Q(department_id=mgr_emp.department_id) | Q(department__manager_id=user_id) | Q(user_id=user_id))
        else:
            qs = qs.filter(Q(department__manager_id=user_id) | Q(user_id=user_id))
        
    employees = qs[skip:skip+limit]
    return [
        {
            'id': e.id,
            'employee_id': e.employee_id,
            'first_name': e.user.first_name if e.user else '',
            'last_name': e.user.last_name if e.user else '',
            'email': e.user.email if e.user else '',
            'department': e.department.name if e.department else '',
            'position': e.position.title if e.position else '',
            'phone': e.phone,
            'status': e.status
        } for e in employees
    ]

def _generate_next_employee_id(department, position) -> str:
    """Sinh mã nhân viên duy nhất theo đúng quy tắc nghiệp vụ, chống xung đột ID."""
    import re
    title = position.title.strip().lower() if position else ''
    is_chairman = 'chủ tịch' in title

    if is_chairman:
        existing_ids = Employee.objects.filter(employee_id__regex=r'^\d{4}$').values_list('employee_id', flat=True)
        max_num = max([int(x) for x in existing_ids], default=0)
        candidate_num = max_num + 1
        while True:
            candidate = f"{candidate_num:04d}"
            if not Employee.objects.filter(employee_id=candidate).exists():
                return candidate
            candidate_num += 1

    prefix_map = {
        'Kỹ thuật': 'KT',
        'Engineering': 'KT',
        'Finance & Accounting': 'FIN',
        'Administration': 'ADM',
        'HR': 'HR',
        'Sales': 'SAL',
        'Pháp chế': 'LEG',
        'Marketing': 'MKT',
        'R&D': 'RND',
    }
    dept_name = department.name if department else ''
    prefix = prefix_map.get(dept_name, 'API')

    existing_ids = Employee.objects.filter(employee_id__startswith=prefix).values_list('employee_id', flat=True)
    max_num = 0
    for eid in existing_ids:
        nums = re.findall(r'\d+$', eid)
        if nums:
            max_num = max(max_num, int(nums[0]))

    # Đảm bảo không trùng với bất kỳ mã nào đang tồn tại
    candidate_num = max(max_num + 1, Employee.objects.count() + 1)
    while True:
        candidate = f"{prefix}{candidate_num:04d}" if candidate_num < 10000 else f"{prefix}{candidate_num % 10000:04d}"
        if not Employee.objects.filter(employee_id=candidate).exists():
            return candidate
        candidate_num += 1

@sync_to_async
def create_employee_db(data: EmployeeCreate):
    import uuid
    import datetime as dt
    from django.db import transaction
    from django.core.exceptions import ValidationError
    from apps.departments.models import Department, Position

    if not data.first_name.strip() or not data.last_name.strip():
        raise ValueError("Họ và tên không được để trống")
    if not data.phone.strip():
        raise ValueError("Số điện thoại không được để trống")

    valid_statuses = dict(Employee.STATUS_CHOICES).keys()
    if data.status not in valid_statuses:
        raise ValueError(f"Trạng thái không hợp lệ. Chỉ chấp nhận: {', '.join(valid_statuses)}")

    with transaction.atomic():
        # Khóa kiểm tra email trùng lặp trong transaction
        if User.objects.select_for_update().filter(email=data.email).exists():
            raise FileExistsError("Email already exists")

        department = None
        if data.department_id is not None:
            department = Department.objects.filter(id=data.department_id).first()
            if not department:
                raise LookupError(f"Phòng ban ID={data.department_id} không tồn tại")

        position = None
        if data.position_id is not None:
            position = Position.objects.filter(id=data.position_id).first()
            if not position:
                raise LookupError(f"Chức vụ ID={data.position_id} không tồn tại")

        username = f"emp_{uuid.uuid4().hex[:8]}"
        while User.objects.filter(username=username).exists():
            username = f"emp_{uuid.uuid4().hex[:8]}"

        user = User.objects.create_user(
            username=username,
            email=data.email,
            password='123456',
            first_name=data.first_name.strip(),
            last_name=data.last_name.strip(),
            role='employee'
        )

        new_employee_id = _generate_next_employee_id(department, position)
        emp = Employee(
            user=user,
            employee_id=new_employee_id,
            department=department,
            position=position,
            phone=data.phone.strip(),
            status=data.status,
            gender="O",
            dob=dt.date(2000, 1, 1),
            join_date=dt.date.today(),
            address="N/A"
        )
        try:
            emp.full_clean()
        except ValidationError as ve:
            # Sẽ tự động rollback cả User vừa tạo nhờ transaction.atomic()
            error_messages = "; ".join([f"{k}: {', '.join(v)}" for k, v in ve.message_dict.items()])
            raise ValueError(error_messages)

        emp.save()
        return emp

@sync_to_async
def get_employee_by_id_db(emp_id: int, user_role: str, user_id: int):
    try:
        e = Employee.objects.select_related('user', 'department', 'position').get(id=emp_id)
    except Employee.DoesNotExist:
        return None

    if e.status == 'inactive' or (e.user and not e.user.is_active):
        return None

    if user_role == 'employee' and e.user_id != user_id:
        raise PermissionError("Bạn chỉ có quyền xem hồ sơ của chính mình")
    elif user_role == 'manager':
        mgr_emp = Employee.objects.filter(user_id=user_id).first()
        mgr_dept_id = mgr_emp.department_id if mgr_emp else None
        is_dept_mgr = (e.department and e.department.manager_id == user_id)
        if e.user_id != user_id and not is_dept_mgr and (not mgr_dept_id or e.department_id != mgr_dept_id):
            raise PermissionError("Manager chỉ được xem nhân sự thuộc phòng ban của mình")

    return {
        'id': e.id,
        'employee_id': e.employee_id,
        'first_name': e.user.first_name if e.user else '',
        'last_name': e.user.last_name if e.user else '',
        'email': e.user.email if e.user else '',
        'department': e.department.name if e.department else '',
        'position': e.position.title if e.position else '',
        'phone': e.phone,
        'status': e.status
    }

@sync_to_async
def update_employee_db(emp_id: int, data: EmployeeUpdate, current_user: Optional[dict] = None):
    from django.db import transaction
    from django.core.exceptions import ValidationError

    with transaction.atomic():
        try:
            emp = Employee.objects.select_related('user', 'department', 'position').select_for_update().get(id=emp_id)
        except Employee.DoesNotExist:
            return None

        if current_user and current_user.get("role") == "manager":
            mgr_id = current_user.get("id")
            mgr_emp = Employee.objects.filter(user_id=mgr_id).first()
            mgr_dept_id = mgr_emp.department_id if mgr_emp else None
            is_dept_mgr = (emp.department and emp.department.manager_id == mgr_id)
            if emp.user_id != mgr_id and not is_dept_mgr and (not mgr_dept_id or emp.department_id != mgr_dept_id):
                raise PermissionError("Manager chỉ được cập nhật nhân sự thuộc phòng ban của mình")

        if data.status is not None:
            valid_statuses = dict(Employee.STATUS_CHOICES).keys()
            if data.status not in valid_statuses:
                raise ValueError(f"Trạng thái không hợp lệ. Chỉ chấp nhận: {', '.join(valid_statuses)}")
            emp.status = data.status

        if data.phone is not None:
            if not data.phone.strip():
                raise ValueError("Số điện thoại không được để trống")
            emp.phone = data.phone.strip()

        if emp.user:
            user_locked = User.objects.select_for_update().get(id=emp.user_id)
            if data.status is not None:
                user_locked.is_active = (data.status != 'inactive')
            if data.email is not None:
                if User.objects.filter(email=data.email).exclude(id=user_locked.id).exists():
                    raise FileExistsError("Email already exists")
                user_locked.email = data.email
            if data.first_name is not None:
                if not data.first_name.strip():
                    raise ValueError("Tên không được để trống")
                user_locked.first_name = data.first_name.strip()
            if data.last_name is not None:
                if not data.last_name.strip():
                    raise ValueError("Họ không được để trống")
                user_locked.last_name = data.last_name.strip()

            try:
                emp.full_clean()
            except ValidationError as ve:
                error_messages = "; ".join([f"{k}: {', '.join(v)}" for k, v in ve.message_dict.items()])
                raise ValueError(error_messages)

            user_locked.save()
            emp.user = user_locked
        else:
            try:
                emp.full_clean()
            except ValidationError as ve:
                error_messages = "; ".join([f"{k}: {', '.join(v)}" for k, v in ve.message_dict.items()])
                raise ValueError(error_messages)

        emp.save()
        return emp

@sync_to_async
def delete_employee_db(emp_id: int):
    from django.db import transaction
    with transaction.atomic():
        try:
            emp = Employee.objects.select_for_update().get(id=emp_id)
            if emp.user_id:
                User.objects.filter(id=emp.user_id).delete()
            else:
                emp.delete()
            return True
        except Employee.DoesNotExist:
            return False

# --- Auth & RBAC Dependencies ---
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    """Giải mã Token và lấy thông tin User hiện tại"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") == "refresh":
            raise HTTPException(status_code=401, detail="Không thể dùng Refresh Token để gọi API")
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token không hợp lệ")
        
        user = await get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=401, detail="Tài khoản không tồn tại hoặc đã bị khóa")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token đã hết hạn")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token không hợp lệ")

class RequireRole:
    """Dependency kiểm tra quyền truy cập dựa trên Role"""
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Quyền truy cập bị từ chối. Tính năng này yêu cầu role: {', '.join(self.allowed_roles)}"
            )
        return current_user

# --- API Endpoints: Auth ---
@app.post("/api/auth/login", response_model=TokenResponse, tags=["Xác thực"])
async def login(login_data: LoginRequest):
    """
    Đăng nhập lấy Token. Nhập JSON {username, password}.
    """
    user = await authenticate_user_db(login_data.username, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Tên đăng nhập hoặc mật khẩu không chính xác")
    
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer",
        "role": user["role"]
    }

@app.post("/api/auth/refresh", response_model=TokenResponse, tags=["Xác thực"])
async def refresh_token(token_data: RefreshTokenRequest):
    """
    Làm mới Access Token bằng Refresh Token.
    """
    try:
        payload = jwt.decode(token_data.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Loại Token không đúng")
        username: str = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Refresh Token không hợp lệ hoặc đã hết hạn")
    
    user = await get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="Tài khoản không tồn tại")
        
    return {
        "access_token": create_access_token(user),
        "refresh_token": create_refresh_token(user),
        "token_type": "bearer",
        "role": user["role"]
    }

# --- API Endpoints: CRUD (Secured & RBAC) ---

@app.get("/api/employees", response_model=List[EmployeeOut], include_in_schema=False)
@app.get("/api/employees/", response_model=List[EmployeeOut], tags=["Nhân viên"])
async def read_employees(skip: int = 0, limit: int = 50, current_user: dict = Depends(get_current_user)):
    """
    Xem danh sách nhân sự.
    - Admin/HR: Xem toàn bộ
    - Manager: Xem nhân sự trong phòng ban của mình
    - Employee: Chỉ xem bản thân
    """
    if skip < 0 or limit <= 0 or limit > 200:
        raise HTTPException(status_code=400, detail="Tham số phân trang không hợp lệ (0 <= skip, 1 <= limit <= 200)")
    return await get_employees_db(skip, limit, current_user['role'], current_user['id'])

@app.get("/api/employees/{emp_id}", response_model=EmployeeOut, tags=["Nhân viên"])
async def read_employee_detail(emp_id: int, current_user: dict = Depends(get_current_user)):
    """
    Xem chi tiết 1 nhân sự theo ID (có kiểm soát phạm vi RBAC).
    """
    try:
        emp = await get_employee_by_id_db(emp_id, current_user['role'], current_user['id'])
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    if not emp:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")
    return emp

@app.post("/api/employees", status_code=201, include_in_schema=False)
@app.post("/api/employees/", status_code=201, tags=["Nhân viên"])
async def create_employee(employee: EmployeeCreate, current_user: dict = Depends(RequireRole(['admin', 'hr']))):
    """
    [Chỉ Admin, HR] Thêm nhân sự mới (Atomic Transaction: User + Employee).
    """
    try:
        emp = await create_employee_db(employee)
        return {
            "message": "Tạo thành công",
            "id": emp.id,
            "employee_id": emp.employee_id,
            "email": emp.user.email if emp.user else ""
        }
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/employees/{emp_id}", tags=["Nhân viên"])
async def update_employee(emp_id: int, employee: EmployeeUpdate, current_user: dict = Depends(RequireRole(['admin', 'hr', 'manager']))):
    """
    [Admin, HR, Manager] Cập nhật thông tin nhân sự (Atomic Transaction + Row Lock).
    """
    try:
        emp = await update_employee_db(emp_id, employee, current_user=current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not emp:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")
    return {
        "message": "Cập nhật thành công",
        "id": emp.id,
        "employee_id": emp.employee_id,
        "first_name": emp.user.first_name if emp.user else "",
        "last_name": emp.user.last_name if emp.user else "",
        "status": emp.status
    }

@app.delete("/api/employees/{emp_id}", status_code=204, tags=["Nhân viên"])
async def delete_employee(emp_id: int, current_user: dict = Depends(RequireRole(['admin']))):
    """
    [Chỉ Admin] Xóa nhân sự. HR cũng không được phép xóa hoàn toàn.
    """
    success = await delete_employee_db(emp_id)
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy")
    return None

if __name__ == "__main__":
    import uvicorn
    print("Đang khởi động Enterprise API Server tại http://127.0.0.1:8001")
    uvicorn.run("fastapi_main:app", host="127.0.0.1", port=8001, reload=True)
