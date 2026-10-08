from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Attendance

@login_required
def attendance_list(request):
    records = Attendance.objects.select_related('employee', 'employee__user', 'employee__department').order_by('-date')
    if hasattr(request.user, 'role') and request.user.role == 'employee':
        records = records.filter(employee__user=request.user)
    return render(request, 'attendance.html', {'records': records})
