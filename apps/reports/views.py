from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.employees.models import Employee
from apps.departments.models import Department
from apps.payroll.models import Payroll
from django.db.models import Count, Sum
import json

@login_required
def reports_list(request):
    if request.user.role == 'employee':
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Chỉ quản lý mới được xem báo cáo.")

    # 1. Headcount by Department
    dept_stats = Department.objects.annotate(emp_count=Count('employees')).filter(emp_count__gt=0)
    dept_labels = json.dumps([d.name for d in dept_stats])
    dept_counts = json.dumps([d.emp_count for d in dept_stats])

    # 2. Total Salary Cost by Department
    payroll_stats = Payroll.objects.filter(status='paid').values('employee__department__name').annotate(total_cost=Sum('gross_salary'))
    salary_labels = json.dumps([p['employee__department__name'] or 'Unknown' for p in payroll_stats])
    salary_costs = json.dumps([float(p['total_cost'] or 0) for p in payroll_stats])

    context = {
        'total_employees': Employee.objects.count(),
        'dept_labels': dept_labels,
        'dept_counts': dept_counts,
        'salary_labels': salary_labels,
        'salary_costs': salary_costs,
    }
    return render(request, 'reports.html', context)
