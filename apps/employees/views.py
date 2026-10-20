from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Employee
from apps.departments.models import Department
from django.db.models import Q

@login_required
def employees_list(request):
    search_query = request.GET.get('q', '')
    department_id = request.GET.get('department', '')
    status = request.GET.get('status', '')

    employees = Employee.objects.select_related('user', 'department', 'position')

    if search_query:
        from django.db.models.functions import Concat
        from django.db.models import Value
        employees = employees.annotate(
            full_name_vn=Concat('user__last_name', Value(' '), 'user__first_name'),
            full_name_en=Concat('user__first_name', Value(' '), 'user__last_name')
        ).filter(
            Q(full_name_vn__icontains=search_query) |
            Q(full_name_en__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__role__icontains=search_query) |
            Q(employee_id__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(department__name__icontains=search_query) |
            Q(position__title__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    if department_id:
        try:
            employees = employees.filter(department_id=int(department_id))
        except ValueError:
            pass
        
    if status:
        employees = employees.filter(status=status)

    departments = Department.objects.all()

    context = {
        'employees': employees,
        'departments': departments,
        'search_query': search_query,
        'selected_department': department_id,
        'selected_status': status,
    }
    return render(request, 'employees.html', context)

@login_required
def profile(request, id):
    employee = get_object_or_404(Employee.objects.select_related('user', 'department', 'position', 'manager__user'), id=id)
    return render(request, 'employee_profile.html', {'employee': employee})

from django.db.models import Count, Sum
from apps.departments.models import Department
from apps.leave.models import LeaveRequest
from apps.attendance.models import Attendance
from django.utils import timezone

@login_required
def dashboard(request):
    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(status='active').count()
    total_departments = Department.objects.count()
    
    today = timezone.now().date()
    today_attendance = Attendance.objects.filter(date=today).count()
    pending_leaves = LeaveRequest.objects.filter(status='pending').count()
    
    recent_leaves = LeaveRequest.objects.select_related('employee', 'employee__user').order_by('-created_at')[:5]
    
    # Department chart data
    dept_stats = Department.objects.annotate(emp_count=Count('employees')).filter(emp_count__gt=0)
    import json
    dept_labels = json.dumps([d.name for d in dept_stats])
    dept_counts = json.dumps([d.emp_count for d in dept_stats])
    
    context = {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'total_departments': total_departments,
        'today_attendance': today_attendance,
        'pending_leaves': pending_leaves,
        'recent_leaves': recent_leaves,
        'dept_labels': dept_labels,
        'dept_counts': dept_counts,
    }
    return render(request, 'dashboard.html', context)
from django.contrib import messages
from django.shortcuts import redirect
from django.db import transaction
from django.http import JsonResponse
from apps.accounts.models import User
import datetime

@login_required
def my_profile(request):
    user = request.user
    
    with transaction.atomic():
        employee, _ = Employee.objects.get_or_create(
            user=user,
            defaults={
                'employee_id': f"ADM{user.id:04d}",
                'join_date': datetime.date.today(),
                'phone': '0000000000'
            }
        )
        
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        
        if email and User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, "Email này đã được sử dụng bởi một tài khoản khác!")
            return redirect('employees:my_profile')
            
        with transaction.atomic():
            user.first_name = first_name
            user.last_name = last_name
            if email:
                user.email = email
            user.save()
            
            if 'avatar' in request.FILES:
                employee.avatar = request.FILES['avatar']
                employee.save()
                
        messages.success(request, "Hồ sơ đã được cập nhật thành công!")
        return redirect('employees:my_profile')
        
    return render(request, 'my_profile.html', {'employee': employee, 'user': user})

def api_employees(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'detail': 'Yêu cầu đăng nhập để truy cập dữ liệu.'}, status=401)
    if request.method != 'GET':
        return JsonResponse({'status': 'error', 'detail': 'Method not allowed'}, status=405)

    qs = Employee.objects.select_related('user', 'department', 'position').exclude(status='inactive').filter(user__is_active=True).order_by('id')
    user_role = getattr(request.user, 'role', 'employee')
    if user_role == 'employee':
        qs = qs.filter(user=request.user)
    elif user_role == 'manager':
        mgr_emp = Employee.objects.filter(user=request.user).first()
        if mgr_emp and mgr_emp.department_id:
            qs = qs.filter(Q(department_id=mgr_emp.department_id) | Q(department__manager=request.user) | Q(user=request.user))
        else:
            qs = qs.filter(Q(department__manager=request.user) | Q(user=request.user))

    employees = qs[:50]
    data = []
    for emp in employees:
        data.append({
            'id': emp.id,
            'employee_id': emp.employee_id,
            'full_name': emp.user.get_full_name() if emp.user else '',
            'email': emp.user.email if emp.user else '',
            'department': emp.department.name if emp.department else '',
            'position': emp.position.title if emp.position else '',
            'phone': emp.phone,
            'status': emp.status
        })
    return JsonResponse({'status': 'success', 'count': len(data), 'data': data})


@login_required
def global_search(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({
            'status': 'success',
            'query': '',
            'employees': [],
            'departments': [],
            'quick_links': []
        })

    from django.db.models.functions import Concat
    from django.db.models import Value
    from django.urls import reverse

    # 1. Search employees (comprehensive)
    emp_qs = Employee.objects.select_related('user', 'department', 'position').annotate(
        full_name_vn=Concat('user__last_name', Value(' '), 'user__first_name'),
        full_name_en=Concat('user__first_name', Value(' '), 'user__last_name')
    ).filter(
        Q(full_name_vn__icontains=q) |
        Q(full_name_en__icontains=q) |
        Q(user__first_name__icontains=q) |
        Q(user__last_name__icontains=q) |
        Q(user__username__icontains=q) |
        Q(user__role__icontains=q) |
        Q(employee_id__icontains=q) |
        Q(user__email__icontains=q) |
        Q(department__name__icontains=q) |
        Q(position__title__icontains=q) |
        Q(phone__icontains=q)
    )[:8]

    employees_data = []
    for e in emp_qs:
        name = e.user.get_full_name() if e.user else e.employee_id
        if not name.strip():
            name = e.user.username if e.user else e.employee_id
        employees_data.append({
            'id': e.id,
            'name': name,
            'username': e.user.username if e.user else '',
            'role': e.user.get_role_display() if e.user else '',
            'employee_id': e.employee_id,
            'department': e.department.name if e.department else 'Chưa phân bổ',
            'position': e.position.title if e.position else 'Chưa có chức vụ',
            'avatar_url': e.avatar.url if e.avatar else '',
            'initials': ((e.user.first_name[:1] if e.user and e.user.first_name else '') + (e.user.last_name[:1] if e.user and e.user.last_name else '')).upper() or 'NV',
            'url': reverse('employees:profile', args=[e.id])
        })

    # 2. Search departments
    dept_qs = Department.objects.filter(
        Q(name__icontains=q) | Q(description__icontains=q)
    )[:4]
    departments_data = []
    for d in dept_qs:
        departments_data.append({
            'id': d.id,
            'name': d.name,
            'count': d.employees.count(),
            'manager': d.manager.get_full_name() if d.manager else 'Chưa phân công',
            'url': reverse('employees:list') + f'?department={d.id}'
        })

    # 3. System quick links
    all_links = [
        {'title': 'Danh sách Nhân viên', 'url': reverse('employees:list'), 'icon': 'users', 'keywords': 'nhan vien employee danh sach nhan su danh ba'},
        {'title': 'Danh sách Phòng ban', 'url': reverse('departments:list'), 'icon': 'network', 'keywords': 'phong ban department co cau to chuc phong ban'},
        {'title': 'Lịch sử Chấm công', 'url': reverse('attendance:list'), 'icon': 'clock', 'keywords': 'cham cong attendance diem danh gio vao ra ca lam'},
        {'title': 'Đơn xin nghỉ phép', 'url': reverse('leave:list'), 'icon': 'calendar-off', 'keywords': 'nghi phep leave don phep xin nghi nghi om nghi thai san'},
        {'title': 'Quản lý Bảng lương', 'url': reverse('payroll:list'), 'icon': 'banknote', 'keywords': 'bang luong payroll tien luong luong thang thu nhap thue'},
        {'title': 'Đánh giá hiệu suất KPI', 'url': reverse('performance:list'), 'icon': 'trending-up', 'keywords': 'danh gia performance kpi nang luc xep loai'},
        {'title': 'Báo cáo & Phân tích', 'url': reverse('reports:list'), 'icon': 'pie-chart', 'keywords': 'bao cao reports thong ke phan tich bieu do'},
        {'title': 'Trung tâm Thông báo', 'url': reverse('notifications:list'), 'icon': 'bell', 'keywords': 'thong bao notifications tin nhan canh bao'},
        {'title': 'Hồ sơ cá nhân', 'url': reverse('employees:my_profile'), 'icon': 'user', 'keywords': 'ho so ca nhan my profile thong tin tai khoan'},
    ]
    matched_links = []
    q_lower = q.lower()
    for link in all_links:
        if q_lower in link['title'].lower() or q_lower in link['keywords']:
            matched_links.append(link)

    return JsonResponse({
        'status': 'success',
        'query': q,
        'total_results': len(employees_data) + len(departments_data) + len(matched_links),
        'employees': employees_data,
        'departments': departments_data,
        'quick_links': matched_links[:4]
    })

