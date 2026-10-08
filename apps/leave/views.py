from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import LeaveRequest

@login_required
def leave_list(request):
    requests = LeaveRequest.objects.select_related('employee', 'employee__user', 'employee__department').order_by('-created_at')
    if hasattr(request.user, 'role') and request.user.role == 'employee':
        requests = requests.filter(employee__user=request.user)
    return render(request, 'leave.html', {'requests': requests})
