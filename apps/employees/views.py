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
            full_name=Concat('user__first_name', Value(' '), 'user__last_name')
        ).filter(
            Q(full_name__icontains=search_query) | 
            Q(employee_id__icontains=search_query) |
            Q(user__email__icontains=search_query)
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
    employee = get_object_or_404(Employee.objects.select_related('user', 'department', 'position'), id=id)
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
import datetime

@login_required
def my_profile(request):
    user = request.user
    
    try:
        employee = user.employee_profile
    except Employee.DoesNotExist:
        employee = Employee.objects.create(
            user=user, 
            employee_id=f"EMP-ADMIN-{user.id}", 
            join_date=datetime.date.today()
        )
        
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        
        if 'avatar' in request.FILES:
            employee.avatar = request.FILES['avatar']
            employee.save()
            
        messages.success(request, "Hồ sơ đã được cập nhật thành công!")
        return redirect('employees:my_profile')
        
    return render(request, 'my_profile.html', {'employee': employee, 'user': user})
from django.http import JsonResponse

def api_employees(request):
    employees = Employee.objects.select_related('user', 'department', 'position').all()[:50]
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
