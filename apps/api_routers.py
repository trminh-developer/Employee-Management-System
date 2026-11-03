"""
Modular FastAPI Routers for TMNexora Enterprise HR API.
Covers all remaining domain modules with JWT Auth, 4-tier RBAC, and ACID transactions:
- Auth Profile (/api/auth/me)
- Departments & Positions (/api/departments, /api/positions)
- Attendance & Real-time Check-in/Check-out (/api/attendance)
- 2-Level Leave Request Workflow (/api/leaves)
- Payroll Engine & Payslips (/api/payrolls)
- Performance Reviews / KPI (/api/performance)
- Notifications & N8N Webhook Trigger (/api/notifications)
- Executive Reports & Analytics (/api/reports)
"""

from datetime import date, time, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Callable, List, Optional

from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from apps.accounts.models import User
from apps.attendance.models import Attendance
from apps.departments.models import Department, Position
from apps.employees.models import Employee
from apps.leave.models import LeaveRequest
from apps.notifications.models import Notification
from apps.payroll.models import Payroll
from apps.performance.models import PerformanceReview


# ==============================================================================
# PYDANTIC SCHEMAS
# ==============================================================================

# --- 1. Auth Profile ---
class UserProfileOut(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    role: str
    is_active: bool
    employee_pk: Optional[int] = None
    employee_code: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None


# --- 2. Departments & Positions ---
class PositionOut(BaseModel):
    id: int
    title: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None


class PositionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    department_id: Optional[int] = None


class PositionUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    department_id: Optional[int] = None


class DepartmentOut(BaseModel):
    id: int
    name: str
    description: str
    manager_id: Optional[int] = None
    manager_name: Optional[str] = None
    parent_id: Optional[int] = None
    parent_name: Optional[str] = None
    budget: float
    employee_count: int = 0
    created_at: datetime
    updated_at: datetime


class DepartmentDetailOut(DepartmentOut):
    positions: List[PositionOut] = []


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    manager_id: Optional[int] = None
    parent_id: Optional[int] = None
    budget: float = Field(default=0, ge=0)


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    manager_id: Optional[int] = None
    parent_id: Optional[int] = None
    budget: Optional[float] = Field(default=None, ge=0)


# --- 3. Attendance ---
class AttendanceOut(BaseModel):
    id: int
    employee_id: int
    employee_code: str
    employee_name: str
    department: Optional[str] = None
    date: date
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: str
    overtime_hours: float
    note: str
    created_at: datetime


class CheckInRequest(BaseModel):
    is_remote: bool = False
    note: str = ""


class CheckOutRequest(BaseModel):
    note: str = ""


class AttendanceCreate(BaseModel):
    employee_id: int
    date: date
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: str = Field(default="present", description="present | late | absent | remote")
    overtime_hours: float = Field(default=0, ge=0)
    note: str = ""


class AttendanceUpdate(BaseModel):
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: Optional[str] = None
    overtime_hours: Optional[float] = Field(default=None, ge=0)
    note: Optional[str] = None


# --- 4. Leave Requests ---
class LeaveOut(BaseModel):
    id: int
    employee_id: int
    employee_code: str
    employee_name: str
    department: Optional[str] = None
    leave_type: str
    start_date: date
    end_date: date
    duration_days: float
    reason: str
    status: str
    created_at: datetime
    updated_at: datetime


class LeaveCreate(BaseModel):
    leave_type: str = Field(..., description="annual | sick | personal | unpaid")
    start_date: date
    end_date: date
    reason: str = Field(..., min_length=3)
    employee_id: Optional[int] = Field(
        default=None,
        description="Bỏ trống nếu tạo đơn cho chính mình; Admin/HR có thể truyền employee_id để tạo hộ."
    )


class LeaveUpdate(BaseModel):
    leave_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reason: Optional[str] = None


class LeaveDecisionRequest(BaseModel):
    comment: str = ""


# --- 5. Payroll ---
class PayrollOut(BaseModel):
    id: int
    employee_id: int
    employee_code: str
    employee_name: str
    department: Optional[str] = None
    month: int
    year: int
    base_salary: float
    allowances: float
    overtime_pay: float
    bonus: float
    tax: float
    insurance: float
    gross_salary: float
    net_salary: float
    status: str
    created_at: datetime
    updated_at: datetime


class PayrollCreate(BaseModel):
    employee_id: int
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020, le=2100)
    base_salary: float = Field(..., ge=0)
    allowances: float = Field(default=0, ge=0)
    overtime_pay: Optional[float] = Field(
        default=None,
        ge=0,
        description="Nếu bỏ trống (null), hệ thống tự động tính từ tổng giờ OT tháng đó * 150% đơn giá giờ."
    )
    bonus: float = Field(default=0, ge=0)
    tax: Optional[float] = Field(default=None, ge=0)
    insurance: Optional[float] = Field(default=None, ge=0)
    auto_calculate_deductions: bool = Field(
        default=True,
        description="Tự động tính BHXH/BHYT/BHTN (10.5%) và Thuế TNCN lũy tiến 7 bậc nếu tax/insurance để trống."
    )
    status: str = Field(default="calculated", description="draft | calculated | reviewed | approved | paid")


class PayrollUpdate(BaseModel):
    base_salary: Optional[float] = Field(default=None, ge=0)
    allowances: Optional[float] = Field(default=None, ge=0)
    overtime_pay: Optional[float] = Field(default=None, ge=0)
    bonus: Optional[float] = Field(default=None, ge=0)
    tax: Optional[float] = Field(default=None, ge=0)
    insurance: Optional[float] = Field(default=None, ge=0)
    status: Optional[str] = None


# --- 6. Performance Reviews (KPI) ---
class PerformanceOut(BaseModel):
    id: int
    employee_id: int
    employee_code: str
    employee_name: str
    department: Optional[str] = None
    reviewer_id: Optional[int] = None
    reviewer_name: Optional[str] = None
    period: str
    score: float
    feedback: str
    created_at: datetime


class PerformanceCreate(BaseModel):
    employee_id: int
    period: str = Field(..., min_length=2, max_length=50, examples=["Q4 2026"])
    score: float = Field(..., ge=0, le=100)
    feedback: str = Field(..., min_length=3)


class PerformanceUpdate(BaseModel):
    period: Optional[str] = Field(default=None, min_length=2, max_length=50)
    score: Optional[float] = Field(default=None, ge=0, le=100)
    feedback: Optional[str] = None


# --- 7. Notifications ---
class NotificationOut(BaseModel):
    id: int
    user_id: int
    username: str
    title: str
    message: str
    category: str
    priority: str
    is_read: bool
    created_at: datetime


class NotificationCreate(BaseModel):
    user_id: int
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    category: str = Field(default="system", max_length=50)
    priority: str = Field(default="normal", description="low | normal | high | critical")


# --- 8. Reports ---
class DepartmentReportItem(BaseModel):
    department_id: int
    department_name: str
    employee_count: int
    headcount_ratio_percent: float
    total_paid_gross_salary: float


class ReportsSummaryOut(BaseModel):
    total_employees: int
    active_employees: int
    total_departments: int
    today_attendance_count: int
    pending_leave_requests: int
    total_paid_payroll_cost: float
    departments_breakdown: List[DepartmentReportItem]


# ==============================================================================
# INTERNAL RBAC & CALCULATION HELPERS (SYNC)
# ==============================================================================

def _serialize_user_profile(u: User) -> dict:
    emp = getattr(u, "employee_profile", None)
    return {
        "id": u.id,
        "username": u.username,
        "email": u.email or "",
        "first_name": u.first_name or "",
        "last_name": u.last_name or "",
        "full_name": u.get_full_name(),
        "role": u.role,
        "is_active": u.is_active,
        "employee_pk": emp.id if emp else None,
        "employee_code": emp.employee_id if emp else None,
        "department": emp.department.name if (emp and emp.department) else None,
        "position": emp.position.title if (emp and emp.position) else None,
    }


def _serialize_department(d: Department, emp_count: Optional[int] = None) -> dict:
    return {
        "id": d.id,
        "name": d.name,
        "description": d.description or "",
        "manager_id": d.manager_id,
        "manager_name": d.manager.get_full_name() if d.manager else None,
        "parent_id": d.parent_id,
        "parent_name": d.parent.name if d.parent else None,
        "budget": float(d.budget or 0),
        "employee_count": emp_count if emp_count is not None else getattr(d, "employee_count", 0),
        "created_at": d.created_at,
        "updated_at": d.updated_at,
    }


def _serialize_position(p: Position) -> dict:
    return {
        "id": p.id,
        "title": p.title,
        "department_id": p.department_id,
        "department_name": p.department.name if p.department else None,
    }


def _serialize_attendance(a: Attendance) -> dict:
    emp = a.employee
    return {
        "id": a.id,
        "employee_id": a.employee_id,
        "employee_code": emp.employee_id if emp else "",
        "employee_name": emp.user.get_full_name() if (emp and emp.user) else "",
        "department": emp.department.name if (emp and emp.department) else None,
        "date": a.date,
        "check_in": a.check_in,
        "check_out": a.check_out,
        "status": a.status,
        "overtime_hours": float(a.overtime_hours or 0),
        "note": a.note or "",
        "created_at": a.created_at,
    }


def _serialize_leave(lr: LeaveRequest) -> dict:
    emp = lr.employee
    return {
        "id": lr.id,
        "employee_id": lr.employee_id,
        "employee_code": emp.employee_id if emp else "",
        "employee_name": emp.user.get_full_name() if (emp and emp.user) else "",
        "department": emp.department.name if (emp and emp.department) else None,
        "leave_type": lr.leave_type,
        "start_date": lr.start_date,
        "end_date": lr.end_date,
        "duration_days": float(lr.duration_days or 0),
        "reason": lr.reason or "",
        "status": lr.status,
        "created_at": lr.created_at,
        "updated_at": lr.updated_at,
    }


def _serialize_payroll(pr: Payroll) -> dict:
    emp = pr.employee
    return {
        "id": pr.id,
        "employee_id": pr.employee_id,
        "employee_code": emp.employee_id if emp else "",
        "employee_name": emp.user.get_full_name() if (emp and emp.user) else "",
        "department": emp.department.name if (emp and emp.department) else None,
        "month": pr.month,
        "year": pr.year,
        "base_salary": float(pr.base_salary or 0),
        "allowances": float(pr.allowances or 0),
        "overtime_pay": float(pr.overtime_pay or 0),
        "bonus": float(pr.bonus or 0),
        "tax": float(pr.tax or 0),
        "insurance": float(pr.insurance or 0),
        "gross_salary": float(pr.gross_salary or 0),
        "net_salary": float(pr.net_salary or 0),
        "status": pr.status,
        "created_at": pr.created_at,
        "updated_at": pr.updated_at,
    }


def _serialize_performance(rv: PerformanceReview) -> dict:
    emp = rv.employee
    rev = rv.reviewer
    return {
        "id": rv.id,
        "employee_id": rv.employee_id,
        "employee_code": emp.employee_id if emp else "",
        "employee_name": emp.user.get_full_name() if (emp and emp.user) else "",
        "department": emp.department.name if (emp and emp.department) else None,
        "reviewer_id": rv.reviewer_id,
        "reviewer_name": rev.user.get_full_name() if (rev and rev.user) else None,
        "period": rv.period,
        "score": float(rv.score or 0),
        "feedback": rv.feedback or "",
        "created_at": rv.created_at,
    }


def _serialize_notification(n: Notification) -> dict:
    return {
        "id": n.id,
        "user_id": n.user_id,
        "username": n.user.username if n.user else "",
        "title": n.title,
        "message": n.message,
        "category": n.category,
        "priority": n.priority,
        "is_read": n.is_read,
        "created_at": n.created_at,
    }


def _employee_scope_q(user_role: str, user_id: int, prefix: str = "employee") -> Optional[Q]:
    """Build Django Q filter enforcing 4-tier RBAC on models referencing Employee."""
    if user_role in ("admin", "hr"):
        return None
    if user_role == "employee":
        return Q(**{f"{prefix}__user_id": user_id})
    # manager scope
    mgr_emp = Employee.objects.filter(user_id=user_id).first()
    q = Q(**{f"{prefix}__department__manager_id": user_id}) | Q(**{f"{prefix}__user_id": user_id})
    if mgr_emp:
        q = q | Q(**{f"{prefix}__manager_id": mgr_emp.id})
        if mgr_emp.department_id:
            q = q | Q(**{f"{prefix}__department_id": mgr_emp.department_id})
    return q


def _can_manager_access_employee(manager_user_id: int, target_emp: Employee) -> bool:
    if target_emp.user_id == manager_user_id:
        return True
    if target_emp.department and target_emp.department.manager_id == manager_user_id:
        return True
    mgr_emp = Employee.objects.filter(user_id=manager_user_id).first()
    if mgr_emp:
        if target_emp.manager_id == mgr_emp.id:
            return True
        if mgr_emp.department_id and target_emp.department_id == mgr_emp.department_id:
            return True
    return False


def _calculate_vietnam_pit(taxable_income: Decimal) -> Decimal:
    """7-bracket progressive Personal Income Tax (VNĐ) per Vietnamese Tax Law."""
    if taxable_income <= 0:
        return Decimal("0.00")
    brackets = [
        (Decimal("5000000"), Decimal("0.05")),
        (Decimal("10000000"), Decimal("0.10")),
        (Decimal("18000000"), Decimal("0.15")),
        (Decimal("32000000"), Decimal("0.20")),
        (Decimal("52000000"), Decimal("0.25")),
        (Decimal("80000000"), Decimal("0.30")),
    ]
    tax = Decimal("0")
    prev_limit = Decimal("0")
    for upper, rate in brackets:
        if taxable_income > prev_limit:
            chunk = min(taxable_income, upper) - prev_limit
            tax += chunk * rate
            prev_limit = upper
        else:
            break
    if taxable_income > Decimal("80000000"):
        tax += (taxable_income - Decimal("80000000")) * Decimal("0.35")
    return tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ==============================================================================
# ROUTER FACTORY (BINDS AUTH DEPENDENCIES FROM fastapi_main.py)
# ==============================================================================

def register_enterprise_routers(app, get_current_user: Callable, RequireRole: Any) -> None:
    """Attach all domain routers to the FastAPI instance."""

    # --------------------------------------------------------------------------
    # 1. AUTH CURRENT USER PROFILE
    # --------------------------------------------------------------------------
    auth_extra_router = APIRouter(prefix="/api/auth", tags=["Xác thực"])

    @sync_to_async
    def _get_me_db(user_id: int):
        u = User.objects.select_related(
            "employee_profile",
            "employee_profile__department",
            "employee_profile__position",
        ).filter(id=user_id).first()
        if not u:
            return None
        return _serialize_user_profile(u)

    @auth_extra_router.get("/me", response_model=UserProfileOut)
    async def read_current_user_profile(current_user: dict = Depends(get_current_user)):
        """Xem thông tin tài khoản và hồ sơ nhân viên của chính người dùng đang đăng nhập."""
        profile = await _get_me_db(current_user["id"])
        if not profile:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
        return profile

    # --------------------------------------------------------------------------
    # 2. DEPARTMENTS & POSITIONS
    # --------------------------------------------------------------------------
    dept_router = APIRouter(prefix="/api/departments", tags=["Phòng ban & Chức danh"])
    pos_router = APIRouter(prefix="/api/positions", tags=["Phòng ban & Chức danh"])

    @sync_to_async
    def _list_departments_db(q: Optional[str]):
        qs = Department.objects.select_related("manager", "parent").annotate(
            employee_count=Count("employees")
        ).order_by("name")
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(description__icontains=q)
                | Q(manager__first_name__icontains=q)
                | Q(manager__last_name__icontains=q)
                | Q(parent__name__icontains=q)
            )
        return [_serialize_department(d) for d in qs]

    @sync_to_async
    def _get_department_db(dept_id: int):
        d = Department.objects.select_related("manager", "parent").annotate(
            employee_count=Count("employees")
        ).filter(id=dept_id).first()
        if not d:
            return None
        positions = Position.objects.select_related("department").filter(department_id=dept_id).order_by("id")
        data = _serialize_department(d)
        data["positions"] = [_serialize_position(p) for p in positions]
        return data

    @sync_to_async
    def _create_department_db(payload: DepartmentCreate):
        name_clean = payload.name.strip()
        if not name_clean:
            raise ValueError("Tên phòng ban không được để trống")
        with transaction.atomic():
            if Department.objects.filter(name__iexact=name_clean).exists():
                raise FileExistsError(f"Phòng ban '{name_clean}' đã tồn tại")
            manager = None
            if payload.manager_id is not None:
                manager = User.objects.filter(id=payload.manager_id).first()
                if not manager:
                    raise LookupError(f"Tài khoản quản lý ID={payload.manager_id} không tồn tại")
            parent = None
            if payload.parent_id is not None:
                parent = Department.objects.filter(id=payload.parent_id).first()
                if not parent:
                    raise LookupError(f"Phòng ban cấp trên ID={payload.parent_id} không tồn tại")
            d = Department.objects.create(
                name=name_clean,
                description=payload.description.strip(),
                manager=manager,
                parent=parent,
                budget=Decimal(str(payload.budget)),
            )
            return _serialize_department(d, emp_count=0)

    @sync_to_async
    def _update_department_db(dept_id: int, payload: DepartmentUpdate):
        with transaction.atomic():
            d = Department.objects.select_related("manager", "parent").select_for_update().filter(id=dept_id).first()
            if not d:
                return None
            if payload.name is not None:
                name_clean = payload.name.strip()
                if not name_clean:
                    raise ValueError("Tên phòng ban không được để trống")
                if Department.objects.filter(name__iexact=name_clean).exclude(id=dept_id).exists():
                    raise FileExistsError(f"Phòng ban '{name_clean}' đã tồn tại")
                d.name = name_clean
            if payload.description is not None:
                d.description = payload.description.strip()
            if payload.manager_id is not None:
                manager = User.objects.filter(id=payload.manager_id).first()
                if not manager:
                    raise LookupError(f"Tài khoản quản lý ID={payload.manager_id} không tồn tại")
                d.manager = manager
            if payload.parent_id is not None:
                if payload.parent_id == dept_id:
                    raise ValueError("Phòng ban không thể nhận chính nó làm phòng ban cấp trên")
                parent = Department.objects.select_related("parent").filter(id=payload.parent_id).first()
                if not parent:
                    raise LookupError(f"Phòng ban cấp trên ID={payload.parent_id} không tồn tại")
                curr = parent
                hop = 0
                while curr is not None and hop < 50:
                    if curr.id == dept_id:
                        raise ValueError("Phát hiện vòng lặp phân cấp phòng ban (cyclic hierarchy)")
                    curr = curr.parent
                    hop += 1
                d.parent = parent
            if payload.budget is not None:
                d.budget = Decimal(str(payload.budget))
            d.save()
            emp_cnt = Employee.objects.filter(department_id=d.id).count()
            return _serialize_department(d, emp_count=emp_cnt)

    @sync_to_async
    def _delete_department_db(dept_id: int):
        with transaction.atomic():
            d = Department.objects.select_for_update().filter(id=dept_id).first()
            if not d:
                return False
            d.delete()
            return True

    @dept_router.get("", response_model=List[DepartmentOut], include_in_schema=False)
    @dept_router.get("/", response_model=List[DepartmentOut])
    async def list_departments(q: Optional[str] = None, current_user: dict = Depends(get_current_user)):
        """Xem danh sách phòng ban, trưởng phòng, phòng ban cấp trên, ngân sách và quân số."""
        return await _list_departments_db(q)

    @dept_router.get("/{dept_id}", response_model=DepartmentDetailOut)
    async def get_department(dept_id: int, current_user: dict = Depends(get_current_user)):
        """Xem chi tiết một phòng ban kèm danh sách chức danh chuyên môn trực thuộc."""
        res = await _get_department_db(dept_id)
        if not res:
            raise HTTPException(status_code=404, detail="Không tìm thấy phòng ban")
        return res

    @dept_router.post("", response_model=DepartmentOut, status_code=201, include_in_schema=False)
    @dept_router.post("/", response_model=DepartmentOut, status_code=201)
    async def create_department(
        data: DepartmentCreate,
        current_user: dict = Depends(RequireRole(["admin", "hr"])),
    ):
        """[Admin, HR] Tạo phòng ban mới."""
        try:
            return await _create_department_db(data)
        except FileExistsError as e:
            raise HTTPException(status_code=409, detail=str(e))
        except LookupError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @dept_router.put("/{dept_id}", response_model=DepartmentOut)
    async def update_department(
        dept_id: int,
        data: DepartmentUpdate,
        current_user: dict = Depends(RequireRole(["admin", "hr"])),
    ):
        """[Admin, HR] Cập nhật thông tin phòng ban."""
        try:
            res = await _update_department_db(dept_id, data)
        except FileExistsError as e:
            raise HTTPException(status_code=409, detail=str(e))
        except LookupError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        if not res:
            raise HTTPException(status_code=404, detail="Không tìm thấy phòng ban")
        return res

    @dept_router.delete("/{dept_id}", status_code=204)
    async def delete_department(dept_id: int, current_user: dict = Depends(RequireRole(["admin"]))):
        """[Chỉ Admin] Xóa phòng ban."""
        ok = await _delete_department_db(dept_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Không tìm thấy phòng ban")
        return None

    # --- Positions Endpoints ---
    @sync_to_async
    def _list_positions_db(department_id: Optional[int]):
        qs = Position.objects.select_related("department").order_by("id")
        if department_id is not None:
            qs = qs.filter(department_id=department_id)
        return [_serialize_position(p) for p in qs]

    @sync_to_async
    def _create_position_db(payload: PositionCreate):
        title_clean = payload.title.strip()
        if not title_clean:
            raise ValueError("Tên chức danh không được để trống")
        with transaction.atomic():
            if Position.objects.filter(title__iexact=title_clean).exists():
                raise FileExistsError(f"Chức danh '{title_clean}' đã tồn tại")
            dept = None
            if payload.department_id is not None:
                dept = Department.objects.filter(id=payload.department_id).first()
                if not dept:
                    raise LookupError(f"Phòng ban ID={payload.department_id} không tồn tại")
            p = Position.objects.create(title=title_clean, department=dept)
            return _serialize_position(p)

    @sync_to_async
    def _update_position_db(pos_id: int, payload: PositionUpdate):
        with transaction.atomic():
            p = Position.objects.select_related("department").select_for_update().filter(id=pos_id).first()
            if not p:
                return None
            if payload.title is not None:
                title_clean = payload.title.strip()
                if not title_clean:
                    raise ValueError("Tên chức danh không được để trống")
                if Position.objects.filter(title__iexact=title_clean).exclude(id=pos_id).exists():
                    raise FileExistsError(f"Chức danh '{title_clean}' đã tồn tại")
                p.title = title_clean
            if payload.department_id is not None:
                dept = Department.objects.filter(id=payload.department_id).first()
                if not dept:
                    raise LookupError(f"Phòng ban ID={payload.department_id} không tồn tại")
                p.department = dept
            p.save()
            return _serialize_position(p)

    @sync_to_async
    def _delete_position_db(pos_id: int):
        with transaction.atomic():
            p = Position.objects.select_for_update().filter(id=pos_id).first()
            if not p:
                return False
            p.delete()
            return True

    @pos_router.get("", response_model=List[PositionOut], include_in_schema=False)
    @pos_router.get("/", response_model=List[PositionOut])
    async def list_positions(
        department_id: Optional[int] = None,
        current_user: dict = Depends(get_current_user),
    ):
        """Xem danh sách chức danh định biên (hỗ trợ lọc theo department_id)."""
        return await _list_positions_db(department_id)

    @sync_to_async
    def _get_position_db(pos_id: int):
        p = Position.objects.select_related("department").filter(id=pos_id).first()
        return _serialize_position(p) if p else None

    @pos_router.get("/{pos_id}", response_model=PositionOut)
    async def get_position(pos_id: int, current_user: dict = Depends(get_current_user)):
        """Xem chi tiết một chức danh chuyên môn."""
        res = await _get_position_db(pos_id)
        if not res:
            raise HTTPException(status_code=404, detail="Không tìm thấy chức danh")
        return res

    @pos_router.post("", response_model=PositionOut, status_code=201, include_in_schema=False)
    @pos_router.post("/", response_model=PositionOut, status_code=201)
    async def create_position(
        data: PositionCreate,
        current_user: dict = Depends(RequireRole(["admin", "hr"])),
    ):
        """[Admin, HR] Thêm chức danh chuyên môn mới."""
        try:
            return await _create_position_db(data)
        except FileExistsError as e:
            raise HTTPException(status_code=409, detail=str(e))
        except LookupError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @pos_router.put("/{pos_id}", response_model=PositionOut)
    async def update_position(
        pos_id: int,
        data: PositionUpdate,
        current_user: dict = Depends(RequireRole(["admin", "hr"])),
    ):
        """[Admin, HR] Cập nhật chức danh chuyên môn."""
        try:
            res = await _update_position_db(pos_id, data)
        except FileExistsError as e:
            raise HTTPException(status_code=409, detail=str(e))
        except LookupError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        if not res:
            raise HTTPException(status_code=404, detail="Không tìm thấy chức danh")
        return res

    @pos_router.delete("/{pos_id}", status_code=204)
    async def delete_position(pos_id: int, current_user: dict = Depends(RequireRole(["admin"]))):
        """[Chỉ Admin] Xóa chức danh chuyên môn."""
        ok = await _delete_position_db(pos_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Không tìm thấy chức danh")
        return None

    # --------------------------------------------------------------------------
    # 3. ATTENDANCE & REAL-TIME CHECK-IN / CHECK-OUT
    # --------------------------------------------------------------------------
    att_router = APIRouter(prefix="/api/attendance", tags=["Chấm công"])

    @sync_to_async
    def _list_attendance_db(
        skip: int,
        limit: int,
        user_role: str,
        user_id: int,
        employee_id: Optional[int],
        date_from: Optional[date],
        date_to: Optional[date],
        status_filter: Optional[str],
    ):
        qs = Attendance.objects.select_related(
            "employee", "employee__user", "employee__department"
        ).order_by("-date", "-id")
        scope_q = _employee_scope_q(user_role, user_id)
        if scope_q is not None:
            qs = qs.filter(scope_q)
        if employee_id is not None:
            qs = qs.filter(employee_id=employee_id)
        if date_from is not None:
            qs = qs.filter(date__gte=date_from)
        if date_to is not None:
            qs = qs.filter(date__lte=date_to)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return [_serialize_attendance(a) for a in qs[skip : skip + limit]]

    @sync_to_async
    def _get_attendance_db(att_id: int, user_role: str, user_id: int):
        a = Attendance.objects.select_related(
            "employee", "employee__user", "employee__department"
        ).filter(id=att_id).first()
        if not a:
            return None
        if user_role == "employee" and a.employee.user_id != user_id:
            raise PermissionError("Bạn chỉ được xem dữ liệu chấm công của chính mình")
        if user_role == "manager" and not _can_manager_access_employee(user_id, a.employee):
            raise PermissionError("Manager chỉ được xem chấm công nhân sự thuộc phòng ban mình quản lý")
        return _serialize_attendance(a)

    @sync_to_async
    def _check_in_db(user_id: int, payload: CheckInRequest):
        emp = Employee.objects.select_related("user", "department").filter(user_id=user_id).first()
        if not emp:
            raise LookupError("Tài khoản hiện tại chưa được liên kết với hồ sơ nhân viên (Employee)")
        now_local = timezone.localtime(timezone.now())
        today = now_local.date()
        now_time = now_local.time().replace(microsecond=0)

        with transaction.atomic():
            if Attendance.objects.select_for_update().filter(employee=emp, date=today).exists():
                raise FileExistsError(f"Bạn đã điểm danh Check-in ngày {today} rồi")
            if payload.is_remote:
                att_status = "remote"
            elif now_time > time(8, 30, 0):
                att_status = "late"
            else:
                att_status = "present"

            att = Attendance.objects.create(
                employee=emp,
                date=today,
                check_in=now_time,
                status=att_status,
                overtime_hours=Decimal("0.00"),
                note=payload.note.strip(),
            )
            return _serialize_attendance(att)

    @sync_to_async
    def _check_out_db(user_id: int, payload: CheckOutRequest):
        emp = Employee.objects.select_related("user", "department").filter(user_id=user_id).first()
        if not emp:
            raise LookupError("Tài khoản hiện tại chưa được liên kết với hồ sơ nhân viên (Employee)")
        now_local = timezone.localtime(timezone.now())
        today = now_local.date()
        now_time = now_local.time().replace(microsecond=0)

        with transaction.atomic():
            att = Attendance.objects.select_related(
                "employee", "employee__user", "employee__department"
            ).select_for_update().filter(employee=emp, date=today).first()
            if not att:
                raise LookupError(f"Chưa tìm thấy bản ghi Check-in ngày {today} để Check-out")
            att.check_out = now_time
            # Ca chuẩn kết thúc 17:30 -> tự động tính giờ tăng ca (OT)
            shift_end_minutes = 17 * 60 + 30
            out_minutes = now_time.hour * 60 + now_time.minute
            if out_minutes > shift_end_minutes:
                ot = Decimal(str((out_minutes - shift_end_minutes) / 60)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                att.overtime_hours = ot
            if payload.note.strip():
                att.note = f"{att.note} | {payload.note.strip()}".strip(" |")
            att.save()
            return _serialize_attendance(att)

    @sync_to_async
    def _create_attendance_db(payload: AttendanceCreate):
        valid_statuses = dict(Attendance.STATUS_CHOICES).keys()
        if payload.status not in valid_statuses:
            raise ValueError(f"Trạng thái không hợp lệ. Chỉ chấp nhận: {', '.join(valid_statuses)}")
        with transaction.atomic():
            emp = Employee.objects.select_related("user", "department").filter(id=payload.employee_id).first()
            if not emp:
                raise LookupError(f"Nhân viên ID={payload.employee_id} không tồn tại")
            if Attendance.objects.filter(employee_id=emp.id, date=payload.date).exists():
                raise FileExistsError(f"Nhân viên {emp.employee_id} đã có bản ghi chấm công ngày {payload.date}")
            att = Attendance.objects.create(
                employee=emp,
                date=payload.date,
                check_in=payload.check_in,
                check_out=payload.check_out,
                status=payload.status,
                overtime_hours=Decimal(str(payload.overtime_hours)),
                note=payload.note.strip(),
            )
            return _serialize_attendance(att)

    @sync_to_async
    def _update_attendance_db(att_id: int, payload: AttendanceUpdate):
        valid_statuses = dict(Attendance.STATUS_CHOICES).keys()
        if payload.status is not None and payload.status not in valid_statuses:
            raise ValueError(f"Trạng thái không hợp lệ. Chỉ chấp nhận: {', '.join(valid_statuses)}")
        with transaction.atomic():
            att = Attendance.objects.select_related(
                "employee", "employee__user", "employee__department"
            ).select_for_update().filter(id=att_id).first()
            if not att:
                return None
            if payload.check_in is not None:
                att.check_in = payload.check_in
            if payload.check_out is not None:
                att.check_out = payload.check_out
            if payload.status is not None:
                att.status = payload.status
            if payload.overtime_hours is not None:
                att.overtime_hours = Decimal(str(payload.overtime_hours))
            if payload.note is not None:
                att.note = payload.note.strip()
            att.save()
            return _serialize_attendance(att)

    @sync_to_async
    def _delete_attendance_db(att_id: int):
        with transaction.atomic():
            att = Attendance.objects.select_for_update().filter(id=att_id).first()
            if not att:
                return False
            att.delete()
            return True

    @att_router.get("", response_model=List[AttendanceOut], include_in_schema=False)
    @att_router.get("/", response_model=List[AttendanceOut])
    async def list_attendance(
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=200),
        employee_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        status: Optional[str] = None,
        current_user: dict = Depends(get_current_user),
    ):
        """Xem bảng chấm công theo phạm vi phân quyền RBAC (Admin/HR: toàn bộ, Manager: phòng ban, Employee: cá nhân)."""
        return await _list_attendance_db(
            skip, limit, current_user["role"], current_user["id"], employee_id, date_from, date_to, status
        )

    @att_router.post("/check-in", response_model=AttendanceOut, status_code=201)
    async def check_in_today(data: CheckInRequest = CheckInRequest(), current_user: dict = Depends(get_current_user)):
        """Điểm danh vào ca thời gian thực (tự động phân loại Đúng giờ <= 08:30 / Đi muộn > 08:30 / Làm từ xa)."""
        try:
            return await _check_in_db(current_user["id"], data)
        except LookupError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except FileExistsError as e:
            raise HTTPException(status_code=409, detail=str(e))

    @att_router.post("/check-out", response_model=AttendanceOut)
    async def check_out_today(
        data: CheckOutRequest = CheckOutRequest(), current_user: dict = Depends(get_current_user)
    ):
        """Điểm danh tan ca thời gian thực (tự động tính giờ tăng ca OT nếu sau 17:30)."""
        try:
            return await _check_out_db(current_user["id"], data)
        except LookupError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @att_router.get("/{att_id}", response_model=AttendanceOut)
    async def get_attendance_detail(att_id: int, current_user: dict = Depends(get_current_user)):
        """Xem chi tiết một bản ghi chấm công."""
        try:
            res = await _get_attendance_db(att_id, current_user["role"], current_user["id"])
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        if not res:
            raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi chấm công")
        return res

    @att_router.post("", response_model=AttendanceOut, status_code=201, include_in_schema=False)
    @att_router.post("/", response_model=AttendanceOut, status_code=201)
    async def create_attendance(
        data: AttendanceCreate,
        current_user: dict = Depends(RequireRole(["admin", "hr"])),
    ):
        """[Admin, HR] Tạo hoặc bổ sung công thủ công cho nhân viên."""
        try:
            return await _create_attendance_db(data)
        except FileExistsError as e:
            raise HTTPException(status_code=409, detail=str(e))
        except LookupError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @att_router.put("/{att_id}", response_model=AttendanceOut)
    async def update_attendance(
        att_id: int,
        data: AttendanceUpdate,
        current_user: dict = Depends(RequireRole(["admin", "hr"])),
    ):
        """[Admin, HR] Hiệu chỉnh giờ vào/ra, trạng thái công và giờ tăng ca."""
        try:
            res = await _update_attendance_db(att_id, data)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        if not res:
            raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi chấm công")
        return res

    @att_router.delete("/{att_id}", status_code=204)
    async def delete_attendance(att_id: int, current_user: dict = Depends(RequireRole(["admin", "hr"]))):
        """[Admin, HR] Xóa bản ghi chấm công."""
        ok = await _delete_attendance_db(att_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi chấm công")
        return None

    # --------------------------------------------------------------------------
    # 4. LEAVE REQUESTS (2-LEVEL APPROVAL WORKFLOW)
    # --------------------------------------------------------------------------
    leave_router = APIRouter(prefix="/api/leaves", tags=["Nghỉ phép"])

    @sync_to_async
    def _list_leaves_db(
        skip: int,
        limit: int,
        user_role: str,
        user_id: int,
        status_filter: Optional[str],
        leave_type: Optional[str],
        employee_id: Optional[int],
    ):
        qs = LeaveRequest.objects.select_related(
            "employee", "employee__user", "employee__department"
        ).order_by("-created_at", "-id")
        scope_q = _employee_scope_q(user_role, user_id)
        if scope_q is not None:
            qs = qs.filter(scope_q)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if leave_type:
            qs = qs.filter(leave_type=leave_type)
        if employee_id is not None:
            qs = qs.filter(employee_id=employee_id)
        return [_serialize_leave(lr) for lr in qs[skip : skip + limit]]

    @sync_to_async
    def _get_leave_db(leave_id: int, user_role: str, user_id: int):
        lr = LeaveRequest.objects.select_related(
            "employee", "employee__user", "employee__department"
        ).filter(id=leave_id).first()
        if not lr:
            return None
        if user_role == "employee" and lr.employee.user_id != user_id:
            raise PermissionError("Bạn chỉ được xem đơn nghỉ phép của chính mình")
        if user_role == "manager" and not _can_manager_access_employee(user_id, lr.employee):
            raise PermissionError("Manager chỉ được xem đơn nghỉ phép thuộc phòng ban mình quản lý")
        return _serialize_leave(lr)

    @sync_to_async
    def _create_leave_db(user_role: str, user_id: int, payload: LeaveCreate):
        valid_types = dict(LeaveRequest.TYPE_CHOICES).keys()
        if payload.leave_type not in valid_types:
            raise ValueError(f"Loại nghỉ phép không hợp lệ. Chỉ chấp nhận: {', '.join(valid_types)}")
        with transaction.atomic():
            if payload.employee_id is not None and user_role in ("admin", "hr"):
                emp = Employee.objects.select_related("user", "department").filter(id=payload.employee_id).first()
                if not emp:
                    raise LookupError(f"Nhân viên ID={payload.employee_id} không tồn tại")
            else:
                emp = Employee.objects.select_related("user", "department").filter(user_id=user_id).first()
                if not emp:
                    raise LookupError("Tài khoản chưa liên kết hồ sơ nhân viên (Employee)")

            lr = LeaveRequest(
                employee=emp,
                leave_type=payload.leave_type,
                start_date=payload.start_date,
                end_date=payload.end_date,
                reason=payload.reason.strip(),
                status="pending",
            )
            try:
                lr.save()  # Calls clean() and calculates duration_days automatically
            except ValidationError as ve:
                if hasattr(ve, "message_dict"):
                    msg = "; ".join([f"{k}: {', '.join(v)}" for k, v in ve.message_dict.items()])
                else:
                    msg = "; ".join(ve.messages)
                raise ValueError(msg)
            return _serialize_leave(lr)

    @sync_to_async
    def _update_leave_db(leave_id: int, user_role: str, user_id: int, payload: LeaveUpdate):
        valid_types = dict(LeaveRequest.TYPE_CHOICES).keys()
        if payload.leave_type is not None and payload.leave_type not in valid_types:
            raise ValueError(f"Loại nghỉ phép không hợp lệ. Chỉ chấp nhận: {', '.join(valid_types)}")
        with transaction.atomic():
            lr = LeaveRequest.objects.select_related(
                "employee", "employee__user", "employee__department"
            ).select_for_update().filter(id=leave_id).first()
            if not lr:
                return None
            if user_role not in ("admin", "hr"):
                if lr.employee.user_id != user_id:
                    raise PermissionError("Bạn chỉ được chỉnh sửa đơn nghỉ phép của chính mình")
                if lr.status != "pending":
                    raise ValueError("Chỉ được chỉnh sửa đơn nghỉ phép khi đang ở trạng thái chờ duyệt (pending)")
            if payload.leave_type is not None:
                lr.leave_type = payload.leave_type
            if payload.start_date is not None:
                lr.start_date = payload.start_date
            if payload.end_date is not None:
                lr.end_date = payload.end_date
            if payload.reason is not None:
                lr.reason = payload.reason.strip()
            try:
                lr.save()
            except ValidationError as ve:
                if hasattr(ve, "message_dict"):
                    msg = "; ".join([f"{k}: {', '.join(v)}" for k, v in ve.message_dict.items()])
                else:
                    msg = "; ".join(ve.messages)
                raise ValueError(msg)
            return _serialize_leave(lr)

    @sync_to_async
    def _approve_leave_db(leave_id: int, user_role: str, user_id: int, comment: str):
        with transaction.atomic():
            lr = LeaveRequest.objects.select_related(
                "employee", "employee__user", "employee__department"
            ).select_for_update().filter(id=leave_id).first()
            if not lr:
                return None
            if lr.status in ("approved", "rejected"):
                raise ValueError(f"Đơn nghỉ phép đã ở trạng thái kết thúc ({lr.status}), không thể duyệt lại")

            if user_role == "manager":
                if not _can_manager_access_employee(user_id, lr.employee):
                    raise PermissionError("Manager chỉ được phê duyệt đơn của nhân sự thuộc phòng ban mình")
                if lr.status != "pending":
                    raise ValueError("Đơn này đã qua bước Manager phê duyệt cấp 1")
                lr.status = "approved_manager"
                notif_title = "Đơn xin nghỉ phép đã được Quản lý duyệt cấp 1"
                notif_msg = f"Đơn nghỉ phép ({lr.start_date} đến {lr.end_date}) đã được Manager phê duyệt cấp 1 và chuyển lên Ban Nhân sự."
            else:
                # HR or Admin performs final approval (Level 2)
                lr.status = "approved"
                notif_title = "Đơn xin nghỉ phép đã được Phê duyệt chính thức"
                notif_msg = f"Đơn nghỉ phép ({lr.start_date} đến {lr.end_date}) đã được Ban Nhân sự phê duyệt chính thức."

            if comment.strip():
                notif_msg += f" Ghi chú: {comment.strip()}"
            lr.save()

            if lr.employee and lr.employee.user_id:
                Notification.objects.create(
                    user_id=lr.employee.user_id,
                    title=notif_title,
                    message=notif_msg,
                    category="leave",
                    priority="normal",
                )
            return _serialize_leave(lr)

    @sync_to_async
    def _reject_leave_db(leave_id: int, user_role: str, user_id: int, comment: str):
        with transaction.atomic():
            lr = LeaveRequest.objects.select_related(
                "employee", "employee__user", "employee__department"
            ).select_for_update().filter(id=leave_id).first()
            if not lr:
                return None
            if user_role == "manager":
                if not _can_manager_access_employee(user_id, lr.employee):
                    raise PermissionError("Manager chỉ được từ chối đơn của nhân sự thuộc phòng ban mình")
                if lr.status == "approved":
                    raise ValueError("Manager không thể hủy đơn đã được HR phê duyệt chính thức")
            lr.status = "rejected"
            lr.save()

            if lr.employee and lr.employee.user_id:
                msg = f"Đơn xin nghỉ phép ({lr.start_date} đến {lr.end_date}) đã bị từ chối."
                if comment.strip():
                    msg += f" Lý do: {comment.strip()}"
                Notification.objects.create(
                    user_id=lr.employee.user_id,
                    title="Đơn xin nghỉ phép bị từ chối",
                    message=msg,
                    category="leave",
                    priority="high",
                )
            return _serialize_leave(lr)

    @sync_to_async
    def _delete_leave_db(leave_id: int, user_role: str, user_id: int):
        with transaction.atomic():
            lr = LeaveRequest.objects.select_related("employee").select_for_update().filter(id=leave_id).first()
            if not lr:
                return False
            if user_role != "admin":
                if lr.employee.user_id != user_id:
                    raise PermissionError("Bạn không có quyền xóa đơn nghỉ phép của người khác")
                if lr.status != "pending":
                    raise ValueError("Không thể xóa đơn nghỉ phép đã được đưa vào luồng xét duyệt")
            lr.delete()
            return True

    @leave_router.get("", response_model=List[LeaveOut], include_in_schema=False)
    @leave_router.get("/", response_model=List[LeaveOut])
    async def list_leaves(
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=200),
        status: Optional[str] = None,
        leave_type: Optional[str] = None,
        employee_id: Optional[int] = None,
        current_user: dict = Depends(get_current_user),
    ):
        """Xem danh sách đơn xin nghỉ phép theo phạm vi phân quyền RBAC."""
        return await _list_leaves_db(
            skip, limit, current_user["role"], current_user["id"], status, leave_type, employee_id
        )

    @leave_router.get("/{leave_id}", response_model=LeaveOut)
    async def get_leave_detail(leave_id: int, current_user: dict = Depends(get_current_user)):
        """Xem chi tiết một đơn xin nghỉ phép."""
        try:
            res = await _get_leave_db(leave_id, current_user["role"], current_user["id"])
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        if not res:
            raise HTTPException(status_code=404, detail="Không tìm thấy đơn nghỉ phép")
        return res

    @leave_router.post("", response_model=LeaveOut, status_code=201, include_in_schema=False)
    @leave_router.post("/", response_model=LeaveOut, status_code=201)
    async def create_leave(data: LeaveCreate, current_user: dict = Depends(get_current_user)):
        """Tạo đơn xin nghỉ phép mới (tự động tính số ngày nghỉ duration_days và đưa vào hàng đợi pending)."""
        try:
            return await _create_leave_db(current_user["role"], current_user["id"], data)
        except LookupError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @leave_router.put("/{leave_id}", response_model=LeaveOut)
    async def update_leave(leave_id: int, data: LeaveUpdate, current_user: dict = Depends(get_current_user)):
        """Cập nhật đơn nghỉ phép (nhân viên chỉ sửa được khi đơn còn ở trạng thái pending)."""
        try:
            res = await _update_leave_db(leave_id, current_user["role"], current_user["id"], data)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        if not res:
            raise HTTPException(status_code=404, detail="Không tìm thấy đơn nghỉ phép")
        return res

    @leave_router.post("/{leave_id}/approve", response_model=LeaveOut)
    async def approve_leave(
        leave_id: int,
        decision: LeaveDecisionRequest = LeaveDecisionRequest(),
        current_user: dict = Depends(RequireRole(["admin", "hr", "manager"])),
    ):
        """[Manager, HR, Admin] Phê duyệt đơn nghỉ phép 2 cấp (Manager -> approved_manager; HR/Admin -> approved)."""
        try:
            res = await _approve_leave_db(leave_id, current_user["role"], current_user["id"], decision.comment)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        if not res:
            raise HTTPException(status_code=404, detail="Không tìm thấy đơn nghỉ phép")
        return res

    @leave_router.post("/{leave_id}/reject", response_model=LeaveOut)
    async def reject_leave(
        leave_id: int,
        decision: LeaveDecisionRequest = LeaveDecisionRequest(),
        current_user: dict = Depends(RequireRole(["admin", "hr", "manager"])),
    ):
        """[Manager, HR, Admin] Từ chối đơn nghỉ phép và gửi thông báo phản hồi tự động."""
        try:
            res = await _reject_leave_db(leave_id, current_user["role"], current_user["id"], decision.comment)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        if not res:
            raise HTTPException(status_code=404, detail="Không tìm thấy đơn nghỉ phép")
        return res

    @leave_router.delete("/{leave_id}", status_code=204)
    async def delete_leave(leave_id: int, current_user: dict = Depends(get_current_user)):
        """Hủy đơn nghỉ phép đang chờ duyệt (hoặc Admin xóa vĩnh viễn)."""
        try:
            ok = await _delete_leave_db(leave_id, current_user["role"], current_user["id"])
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        if not ok:
            raise HTTPException(status_code=404, detail="Không tìm thấy đơn nghỉ phép")
        return None

    # --------------------------------------------------------------------------
    # 5. PAYROLL ENGINE & PAYSLIPS
    # --------------------------------------------------------------------------
    payroll_router = APIRouter(prefix="/api/payrolls", tags=["Bảng lương"])

    @sync_to_async
    def _list_payrolls_db(
        skip: int,
        limit: int,
        user_role: str,
        user_id: int,
        month: Optional[int],
        year: Optional[int],
        status_filter: Optional[str],
        employee_id: Optional[int],
    ):
        qs = Payroll.objects.select_related(
            "employee", "employee__user", "employee__department"
        ).order_by("-year", "-month", "-id")
        # Bảo mật tiền lương: chỉ Admin & HR xem toàn công ty; Manager & Employee chỉ xem phiếu lương cá nhân
        if user_role not in ("admin", "hr"):
            qs = qs.filter(employee__user_id=user_id)
        elif employee_id is not None:
            qs = qs.filter(employee_id=employee_id)

        if month is not None:
            qs = qs.filter(month=month)
        if year is not None:
            qs = qs.filter(year=year)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return [_serialize_payroll(p) for p in qs[skip : skip + limit]]

    @sync_to_async
    def _get_payroll_db(payroll_id: int, user_role: str, user_id: int):
        pr = Payroll.objects.select_related(
            "employee", "employee__user", "employee__department"
        ).filter(id=payroll_id).first()
        if not pr:
            return None
        if user_role not in ("admin", "hr") and pr.employee.user_id != user_id:
            raise PermissionError("Bạn chỉ được phép xem phiếu lương cá nhân của chính mình")
        return _serialize_payroll(pr)

    @sync_to_async
    def _create_payroll_db(payload: PayrollCreate):
        valid_statuses = dict(Payroll.STATUS_CHOICES).keys()
        if payload.status not in valid_statuses:
            raise ValueError(f"Trạng thái bảng lương không hợp lệ. Chỉ chấp nhận: {', '.join(valid_statuses)}")

        with transaction.atomic():
            emp = Employee.objects.select_related("user", "department").filter(id=payload.employee_id).first()
            if not emp:
                raise LookupError(f"Nhân viên ID={payload.employee_id} không tồn tại")
            if Payroll.objects.select_for_update().filter(
                employee_id=emp.id, month=payload.month, year=payload.year
            ).exists():
                raise FileExistsError(
                    f"Nhân viên {emp.employee_id} đã có phiếu lương kỳ {payload.month:02d}/{payload.year}"
                )

            base_sal = Decimal(str(payload.base_salary))
            allowances = Decimal(str(payload.allowances))
            bonus = Decimal(str(payload.bonus))

            if payload.overtime_pay is not None:
                ot_pay = Decimal(str(payload.overtime_pay))
            else:
                # Tự động tổng hợp tổng giờ OT từ bảng Attendance trong tháng (22 ngày * 8 giờ, hệ số 150%)
                ot_agg = Attendance.objects.filter(
                    employee_id=emp.id, date__year=payload.year, date__month=payload.month
                ).aggregate(total_ot=Sum("overtime_hours"))
                total_ot_hours = Decimal(str(ot_agg["total_ot"] or 0))
                hourly_rate = base_sal / Decimal("176") if base_sal > 0 else Decimal("0")
                ot_pay = (total_ot_hours * hourly_rate * Decimal("1.5")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )

            gross = base_sal + allowances + ot_pay + bonus

            if payload.insurance is not None:
                insurance = Decimal(str(payload.insurance))
            elif payload.auto_calculate_deductions:
                # BHXH (8%) + BHYT (1.5%) + BHTN (1%) = 10.5% lương cơ bản đóng bảo hiểm
                insurance = (base_sal * Decimal("0.105")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                insurance = Decimal("0.00")

            if payload.tax is not None:
                tax = Decimal(str(payload.tax))
            elif payload.auto_calculate_deductions:
                personal_deduction = Decimal("11000000")
                taxable_income = gross - insurance - personal_deduction
                tax = _calculate_vietnam_pit(taxable_income)
            else:
                tax = Decimal("0.00")

            pr = Payroll(
                employee=emp,
                month=payload.month,
                year=payload.year,
                base_salary=base_sal,
                allowances=allowances,
                overtime_pay=ot_pay,
                bonus=bonus,
                tax=tax,
                insurance=insurance,
                status=payload.status,
            )
            pr.save()

            if pr.status == "paid" and emp.user_id:
                Notification.objects.create(
                    user_id=emp.user_id,
                    title=f"Phiếu lương kỳ {pr.month:02d}/{pr.year} đã được thanh toán",
                    message=f"Lương thực lĩnh (Net): {pr.net_salary:,.0f} VNĐ đã được phát hành.",
                    category="payroll",
                    priority="normal",
                )
            return _serialize_payroll(pr)

    @sync_to_async
    def _update_payroll_db(payroll_id: int, payload: PayrollUpdate):
        valid_statuses = dict(Payroll.STATUS_CHOICES).keys()
        if payload.status is not None and payload.status not in valid_statuses:
            raise ValueError(f"Trạng thái bảng lương không hợp lệ. Chỉ chấp nhận: {', '.join(valid_statuses)}")

        with transaction.atomic():
            pr = Payroll.objects.select_related(
                "employee", "employee__user", "employee__department"
            ).select_for_update().filter(id=payroll_id).first()
            if not pr:
                return None
            prev_status = pr.status
            if payload.base_salary is not None:
                pr.base_salary = Decimal(str(payload.base_salary))
            if payload.allowances is not None:
                pr.allowances = Decimal(str(payload.allowances))
            if payload.overtime_pay is not None:
                pr.overtime_pay = Decimal(str(payload.overtime_pay))
            if payload.bonus is not None:
                pr.bonus = Decimal(str(payload.bonus))
            if payload.tax is not None:
                pr.tax = Decimal(str(payload.tax))
            if payload.insurance is not None:
                pr.insurance = Decimal(str(payload.insurance))
            if payload.status is not None:
                pr.status = payload.status
            pr.save()

            if prev_status != "paid" and pr.status == "paid" and pr.employee and pr.employee.user_id:
                Notification.objects.create(
                    user_id=pr.employee.user_id,
                    title=f"Phiếu lương kỳ {pr.month:02d}/{pr.year} đã được thanh toán",
                    message=f"Lương thực lĩnh (Net): {pr.net_salary:,.0f} VNĐ đã được phát hành.",
                    category="payroll",
                    priority="normal",
                )
            return _serialize_payroll(pr)

    @sync_to_async
    def _delete_payroll_db(payroll_id: int):
        with transaction.atomic():
            pr = Payroll.objects.select_for_update().filter(id=payroll_id).first()
            if not pr:
                return False
            pr.delete()
            return True

    @payroll_router.get("", response_model=List[PayrollOut], include_in_schema=False)
    @payroll_router.get("/", response_model=List[PayrollOut])
    async def list_payrolls(
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=200),
        month: Optional[int] = Query(None, ge=1, le=12),
        year: Optional[int] = Query(None, ge=2020, le=2100),
        status: Optional[str] = None,
        employee_id: Optional[int] = None,
        current_user: dict = Depends(get_current_user),
    ):
        """Xem danh sách bảng lương (Admin/HR xem toàn công ty; Manager/Employee chỉ xem phiếu lương cá nhân)."""
        return await _list_payrolls_db(
            skip, limit, current_user["role"], current_user["id"], month, year, status, employee_id
        )

    @payroll_router.get("/{payroll_id}", response_model=PayrollOut)
    async def get_payroll_detail(payroll_id: int, current_user: dict = Depends(get_current_user)):
        """Xem chi tiết một phiếu lương."""
        try:
            res = await _get_payroll_db(payroll_id, current_user["role"], current_user["id"])
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        if not res:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiếu lương")
        return res

    @payroll_router.post("", response_model=PayrollOut, status_code=201, include_in_schema=False)
    @payroll_router.post("/", response_model=PayrollOut, status_code=201)
    async def create_payroll(
        data: PayrollCreate,
        current_user: dict = Depends(RequireRole(["admin", "hr"])),
    ):
        """[Admin, HR] Tính và lập phiếu lương tháng tự động (OT 150%, BHXH/BHYT/BHTN 10.5%, Thuế TNCN 7 bậc)."""
        try:
            return await _create_payroll_db(data)
        except FileExistsError as e:
            raise HTTPException(status_code=409, detail=str(e))
        except LookupError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @payroll_router.put("/{payroll_id}", response_model=PayrollOut)
    async def update_payroll(
        payroll_id: int,
        data: PayrollUpdate,
        current_user: dict = Depends(RequireRole(["admin", "hr"])),
    ):
        """[Admin, HR] Cập nhật các khoản lương hoặc phê duyệt phát hành phiếu lương (status='paid')."""
        try:
            res = await _update_payroll_db(payroll_id, data)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        if not res:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiếu lương")
        return res

    @payroll_router.delete("/{payroll_id}", status_code=204)
    async def delete_payroll(payroll_id: int, current_user: dict = Depends(RequireRole(["admin"]))):
        """[Chỉ Admin] Xóa phiếu lương."""
        ok = await _delete_payroll_db(payroll_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiếu lương")
        return None

    # --------------------------------------------------------------------------
    # 6. PERFORMANCE REVIEWS (KPI)
    # --------------------------------------------------------------------------
    perf_router = APIRouter(prefix="/api/performance", tags=["Đánh giá hiệu suất (KPI)"])

    @sync_to_async
    def _list_performance_db(
        skip: int,
        limit: int,
        user_role: str,
        user_id: int,
        employee_id: Optional[int],
        period: Optional[str],
    ):
        qs = PerformanceReview.objects.select_related(
            "employee", "employee__user", "employee__department", "reviewer", "reviewer__user"
        ).order_by("-created_at", "-id")
        if user_role == "employee":
            qs = qs.filter(employee__user_id=user_id)
        elif user_role == "manager":
            scope_q = _employee_scope_q("manager", user_id)
            qs = qs.filter(scope_q | Q(reviewer__user_id=user_id))
        if employee_id is not None:
            qs = qs.filter(employee_id=employee_id)
        if period:
            qs = qs.filter(period__icontains=period)
        return [_serialize_performance(rv) for rv in qs[skip : skip + limit]]

    @sync_to_async
    def _get_performance_db(review_id: int, user_role: str, user_id: int):
        rv = PerformanceReview.objects.select_related(
            "employee", "employee__user", "employee__department", "reviewer", "reviewer__user"
        ).filter(id=review_id).first()
        if not rv:
            return None
        if user_role == "employee" and rv.employee.user_id != user_id:
            raise PermissionError("Bạn chỉ được xem đánh giá KPI của chính mình")
        if user_role == "manager":
            is_reviewer = rv.reviewer and rv.reviewer.user_id == user_id
            if not is_reviewer and not _can_manager_access_employee(user_id, rv.employee):
                raise PermissionError("Manager chỉ được xem đánh giá KPI thuộc phòng ban mình quản lý")
        return _serialize_performance(rv)

    @sync_to_async
    def _create_performance_db(user_role: str, user_id: int, payload: PerformanceCreate):
        with transaction.atomic():
            target_emp = Employee.objects.select_related("user", "department").filter(id=payload.employee_id).first()
            if not target_emp:
                raise LookupError(f"Nhân viên ID={payload.employee_id} không tồn tại")
            if user_role == "manager" and not _can_manager_access_employee(user_id, target_emp):
                raise PermissionError("Manager chỉ được đánh giá KPI cho nhân sự thuộc phòng ban mình")

            reviewer_emp = Employee.objects.select_related("user").filter(user_id=user_id).first()
            rv = PerformanceReview.objects.create(
                employee=target_emp,
                reviewer=reviewer_emp,
                period=payload.period.strip(),
                score=Decimal(str(payload.score)),
                feedback=payload.feedback.strip(),
            )
            return _serialize_performance(rv)

    @sync_to_async
    def _update_performance_db(review_id: int, user_role: str, user_id: int, payload: PerformanceUpdate):
        with transaction.atomic():
            rv = PerformanceReview.objects.select_related(
                "employee", "employee__user", "employee__department", "reviewer", "reviewer__user"
            ).select_for_update().filter(id=review_id).first()
            if not rv:
                return None
            if user_role == "manager":
                is_reviewer = rv.reviewer and rv.reviewer.user_id == user_id
                if not is_reviewer and not _can_manager_access_employee(user_id, rv.employee):
                    raise PermissionError("Manager không có quyền sửa đánh giá KPI ngoài phạm vi phòng ban")
            if payload.period is not None:
                rv.period = payload.period.strip()
            if payload.score is not None:
                rv.score = Decimal(str(payload.score))
            if payload.feedback is not None:
                rv.feedback = payload.feedback.strip()
            rv.save()
            return _serialize_performance(rv)

    @sync_to_async
    def _delete_performance_db(review_id: int):
        with transaction.atomic():
            rv = PerformanceReview.objects.select_for_update().filter(id=review_id).first()
            if not rv:
                return False
            rv.delete()
            return True

    @perf_router.get("", response_model=List[PerformanceOut], include_in_schema=False)
    @perf_router.get("/", response_model=List[PerformanceOut])
    async def list_performance_reviews(
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=200),
        employee_id: Optional[int] = None,
        period: Optional[str] = None,
        current_user: dict = Depends(get_current_user),
    ):
        """Xem danh sách đánh giá hiệu suất làm việc (KPI) theo phân quyền RBAC."""
        return await _list_performance_db(
            skip, limit, current_user["role"], current_user["id"], employee_id, period
        )

    @perf_router.get("/{review_id}", response_model=PerformanceOut)
    async def get_performance_detail(review_id: int, current_user: dict = Depends(get_current_user)):
        """Xem chi tiết một bản đánh giá KPI."""
        try:
            res = await _get_performance_db(review_id, current_user["role"], current_user["id"])
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        if not res:
            raise HTTPException(status_code=404, detail="Không tìm thấy bản đánh giá KPI")
        return res

    @perf_router.post("", response_model=PerformanceOut, status_code=201, include_in_schema=False)
    @perf_router.post("/", response_model=PerformanceOut, status_code=201)
    async def create_performance_review(
        data: PerformanceCreate,
        current_user: dict = Depends(RequireRole(["admin", "hr", "manager"])),
    ):
        """[Admin, HR, Manager] Lập phiếu đánh giá KPI định kỳ cho nhân viên."""
        try:
            return await _create_performance_db(current_user["role"], current_user["id"], data)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except LookupError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @perf_router.put("/{review_id}", response_model=PerformanceOut)
    async def update_performance_review(
        review_id: int,
        data: PerformanceUpdate,
        current_user: dict = Depends(RequireRole(["admin", "hr", "manager"])),
    ):
        """[Admin, HR, Manager] Cập nhật điểm KPI và nhận xét chuyên môn."""
        try:
            res = await _update_performance_db(review_id, current_user["role"], current_user["id"], data)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        if not res:
            raise HTTPException(status_code=404, detail="Không tìm thấy bản đánh giá KPI")
        return res

    @perf_router.delete("/{review_id}", status_code=204)
    async def delete_performance_review(
        review_id: int,
        current_user: dict = Depends(RequireRole(["admin", "hr"])),
    ):
        """[Admin, HR] Xóa bản đánh giá KPI."""
        ok = await _delete_performance_db(review_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Không tìm thấy bản đánh giá KPI")
        return None

    # --------------------------------------------------------------------------
    # 7. NOTIFICATIONS & N8N WEBHOOK
    # --------------------------------------------------------------------------
    notif_router = APIRouter(prefix="/api/notifications", tags=["Thông báo"])

    @sync_to_async
    def _list_notifications_db(skip: int, limit: int, user_id: int, unread_only: bool):
        qs = Notification.objects.select_related("user").filter(user_id=user_id).order_by("-created_at", "-id")
        if unread_only:
            qs = qs.filter(is_read=False)
        return [_serialize_notification(n) for n in qs[skip : skip + limit]]

    @sync_to_async
    def _create_notification_db(payload: NotificationCreate):
        valid_priorities = dict(Notification.PRIORITY_CHOICES).keys()
        if payload.priority not in valid_priorities:
            raise ValueError(f"Mức độ ưu tiên không hợp lệ. Chỉ chấp nhận: {', '.join(valid_priorities)}")
        with transaction.atomic():
            target_user = User.objects.filter(id=payload.user_id).first()
            if not target_user:
                raise LookupError(f"Người dùng ID={payload.user_id} không tồn tại")
            n = Notification.objects.create(
                user=target_user,
                title=payload.title.strip(),
                message=payload.message.strip(),
                category=payload.category.strip(),
                priority=payload.priority,
            )
            return _serialize_notification(n)

    @sync_to_async
    def _mark_one_read_db(notif_id: int, user_role: str, user_id: int):
        with transaction.atomic():
            n = Notification.objects.select_related("user").select_for_update().filter(id=notif_id).first()
            if not n:
                return None
            if n.user_id != user_id and user_role != "admin":
                raise PermissionError("Bạn không có quyền thao tác thông báo của người khác")
            n.is_read = True
            n.save(update_fields=["is_read"])
            return _serialize_notification(n)

    @sync_to_async
    def _mark_all_read_db(user_id: int):
        with transaction.atomic():
            return Notification.objects.filter(user_id=user_id, is_read=False).update(is_read=True)

    @sync_to_async
    def _delete_notification_db(notif_id: int, user_role: str, user_id: int):
        with transaction.atomic():
            n = Notification.objects.select_for_update().filter(id=notif_id).first()
            if not n:
                return False
            if n.user_id != user_id and user_role != "admin":
                raise PermissionError("Bạn không có quyền xóa thông báo của người khác")
            n.delete()
            return True

    @notif_router.get("", response_model=List[NotificationOut], include_in_schema=False)
    @notif_router.get("/", response_model=List[NotificationOut])
    async def list_notifications(
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=200),
        unread_only: bool = False,
        current_user: dict = Depends(get_current_user),
    ):
        """Xem danh sách thông báo cá nhân của người dùng đang đăng nhập."""
        return await _list_notifications_db(skip, limit, current_user["id"], unread_only)

    @notif_router.post("", response_model=NotificationOut, status_code=201, include_in_schema=False)
    @notif_router.post("/", response_model=NotificationOut, status_code=201)
    async def send_notification(
        data: NotificationCreate,
        current_user: dict = Depends(RequireRole(["admin", "hr", "manager"])),
    ):
        """[Admin, HR, Manager] Gửi thông báo đến người dùng (tự động kích hoạt N8N Webhook bất đồng bộ)."""
        try:
            return await _create_notification_db(data)
        except LookupError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @notif_router.patch("/{notif_id}/read", response_model=NotificationOut)
    async def mark_notification_read(notif_id: int, current_user: dict = Depends(get_current_user)):
        """Đánh dấu một thông báo là đã đọc."""
        try:
            res = await _mark_one_read_db(notif_id, current_user["role"], current_user["id"])
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        if not res:
            raise HTTPException(status_code=404, detail="Không tìm thấy thông báo")
        return res

    @notif_router.post("/read-all")
    async def mark_all_notifications_read(current_user: dict = Depends(get_current_user)):
        """Đánh dấu toàn bộ thông báo chưa đọc của bản thân thành đã đọc."""
        updated = await _mark_all_read_db(current_user["id"])
        return {"status": "completed", "updated_count": updated}

    @notif_router.delete("/{notif_id}", status_code=204)
    async def delete_notification(notif_id: int, current_user: dict = Depends(get_current_user)):
        """Xóa một thông báo của bản thân (hoặc Admin xóa)."""
        try:
            ok = await _delete_notification_db(notif_id, current_user["role"], current_user["id"])
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        if not ok:
            raise HTTPException(status_code=404, detail="Không tìm thấy thông báo")
        return None

    # --------------------------------------------------------------------------
    # 8. REPORTS & EXECUTIVE ANALYTICS
    # --------------------------------------------------------------------------
    reports_router = APIRouter(prefix="/api/reports", tags=["Báo cáo & Thống kê"])

    @sync_to_async
    def _get_reports_summary_db():
        total_employees = Employee.objects.count()
        active_employees = Employee.objects.filter(status__in=["active", "remote"]).count()
        total_departments = Department.objects.count()
        today = timezone.localtime(timezone.now()).date()
        today_attendance = Attendance.objects.filter(date=today).count()
        pending_leaves = LeaveRequest.objects.filter(status__in=["pending", "approved_manager"]).count()

        dept_qs = Department.objects.annotate(emp_count=Count("employees")).order_by("-emp_count", "name")
        payroll_by_dept = {
            row["employee__department_id"]: float(row["total_cost"] or 0)
            for row in Payroll.objects.filter(status="paid")
            .values("employee__department_id")
            .annotate(total_cost=Sum("gross_salary"))
        }

        total_paid_cost = sum(payroll_by_dept.values())
        breakdown = []
        for d in dept_qs:
            ratio = round((d.emp_count / total_employees) * 100, 1) if total_employees > 0 else 0.0
            breakdown.append(
                {
                    "department_id": d.id,
                    "department_name": d.name,
                    "employee_count": d.emp_count,
                    "headcount_ratio_percent": ratio,
                    "total_paid_gross_salary": payroll_by_dept.get(d.id, 0.0),
                }
            )

        return {
            "total_employees": total_employees,
            "active_employees": active_employees,
            "total_departments": total_departments,
            "today_attendance_count": today_attendance,
            "pending_leave_requests": pending_leaves,
            "total_paid_payroll_cost": total_paid_cost,
            "departments_breakdown": breakdown,
        }

    @reports_router.get("/summary", response_model=ReportsSummaryOut)
    async def get_executive_reports_summary(
        current_user: dict = Depends(RequireRole(["admin", "hr", "manager"])),
    ):
        """[Admin, HR, Manager] Báo cáo tổng hợp định biên nhân sự, tỷ trọng phòng ban, chấm công và quỹ lương."""
        return await _get_reports_summary_db()

    # Register all routers onto app
    app.include_router(auth_extra_router)
    app.include_router(dept_router)
    app.include_router(pos_router)
    app.include_router(att_router)
    app.include_router(leave_router)
    app.include_router(payroll_router)
    app.include_router(perf_router)
    app.include_router(notif_router)
    app.include_router(reports_router)
