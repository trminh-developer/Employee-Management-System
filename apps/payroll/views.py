from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Payroll

@login_required
def payroll_list(request):
    records = Payroll.objects.select_related('employee', 'employee__user', 'employee__department').order_by('-year', '-month')
    if hasattr(request.user, 'role') and request.user.role == 'employee':
        records = records.filter(employee__user=request.user)
    return render(request, 'payroll.html', {'records': records})
