from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import User

@login_required
def user_list(request):
    if request.user.role != 'admin':
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")
        
    search_query = request.GET.get('q', '')
    role_filter = request.GET.get('role', '')
    
    users = User.objects.all().order_by('-date_joined')
    
    if search_query:
        from django.db.models import Q
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
        
    if role_filter:
        users = users.filter(role=role_filter)
        
    return render(request, 'accounts/user_list.html', {'users': users})
