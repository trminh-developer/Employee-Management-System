from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def attendance_list(request):
    return render(request, 'attendance.html')
