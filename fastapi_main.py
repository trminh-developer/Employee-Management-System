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

# Khởi tạo FastAPI App
app = FastAPI(
    title="Enterprise HR API", 
    description="Hệ thống API Quản lý Nhân sự với RBAC (Role-Based Access Control)", 
    version="2.0.0"
)

# Middleware tự động dọn dẹp kết nối Database cũ/chết của Django
@app.middleware("http")
async def db_session_middleware(request, call_next):
    close_old_connections()
    try:
        response = await call_next(request)
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

# --- Schemas ---
class LoginRequest(BaseModel):
    username: str
    password: str

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
    user = authenticate(username=username, password=password)
    if user is not None:
        return {"id": user.id, "username": user.username, "role": user.role}
    return None

@sync_to_async
def get_user_by_username(username: str):
    try:
        user = User.objects.get(username=username)
        return {"id": user.id, "username": user.username, "role": user.role}
    except User.DoesNotExist:
        return None

@sync_to_async
def get_employees_db(skip: int, limit: int, user_role: str, user_id: int):
    # RBAC Data Filtering:
    # Admin/HR: Xem toàn bộ nhân sự
    # Manager: Chỉ xem nhân sự trong phòng ban của mình (Ví dụ đơn giản hóa)
    # Employee: Chỉ xem được thông tin của chính mình
    qs = Employee.objects.select_related('user', 'department', 'position').all()
    
    if user_role == 'employee':
        qs = qs.filter(user_id=user_id)
        
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

@sync_to_async
def create_employee_db(data: EmployeeCreate):
    if User.objects.filter(email=data.email).exists():
        raise ValueError("Email already exists")
    import uuid, datetime
    username = str(uuid.uuid4())[:8]
    user = User.objects.create_user(
        username=username,
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
        role='employee'
    )
    emp_count = Employee.objects.count() + 1
    new_employee_id = f"EMP-API-{emp_count:04d}"
    emp = Employee.objects.create(
        user=user,
        employee_id=new_employee_id,
        department_id=data.department_id,
        position_id=data.position_id,
        phone=data.phone,
        status=data.status,
        gender="Other",
        dob=datetime.date(2000, 1, 1),
        join_date=datetime.date.today(),
        address="N/A"
    )
    return emp

@sync_to_async
def update_employee_db(emp_id: int, data: EmployeeUpdate):
    try:
        emp = Employee.objects.select_related('user').get(id=emp_id)
        if data.first_name is not None:
            emp.user.first_name = data.first_name
        if data.last_name is not None:
            emp.user.last_name = data.last_name
        if data.email is not None:
            emp.user.email = data.email
        emp.user.save()
        if data.phone is not None:
            emp.phone = data.phone
        if data.status is not None:
            emp.status = data.status
        emp.save()
        return emp
    except Employee.DoesNotExist:
        return None

@sync_to_async
def delete_employee_db(emp_id: int):
    try:
        emp = Employee.objects.get(id=emp_id)
        if emp.user:
            emp.user.delete()
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
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token không hợp lệ")
        
        # Có thể dùng luôn role từ payload để tiết kiệm query DB, nhưng query DB sẽ an toàn hơn nếu role bị đổi
        user = await get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=401, detail="Tài khoản không tồn tại")
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

@app.get("/api/employees/", response_model=List[EmployeeOut], tags=["Nhân viên"])
async def read_employees(skip: int = 0, limit: int = 50, current_user: dict = Depends(get_current_user)):
    """
    Xem danh sách nhân sự.
    - Admin/HR: Xem toàn bộ
    - Manager: Xem giới hạn
    - Employee: Chỉ xem bản thân
    """
    return await get_employees_db(skip, limit, current_user['role'], current_user['id'])

@app.post("/api/employees/", status_code=201, tags=["Nhân viên"])
async def create_employee(employee: EmployeeCreate, current_user: dict = Depends(RequireRole(['admin', 'hr']))):
    """
    [Chỉ Admin, HR] Thêm nhân sự mới.
    """
    try:
        emp = await create_employee_db(employee)
        return {"message": "Tạo thành công", "employee_id": emp.employee_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/employees/{emp_id}", tags=["Nhân viên"])
async def update_employee(emp_id: int, employee: EmployeeUpdate, current_user: dict = Depends(RequireRole(['admin', 'hr', 'manager']))):
    """
    [Admin, HR, Manager] Cập nhật thông tin nhân sự.
    """
    emp = await update_employee_db(emp_id, employee)
    if not emp:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")
    return {"message": "Cập nhật thành công"}

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
