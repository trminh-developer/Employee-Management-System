from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import PerformanceReview
from django.db.models import Q

@login_required
def performance_list(request):
    search_query = request.GET.get('q', '')
    
    reviews = PerformanceReview.objects.select_related('employee__user', 'reviewer__user').order_by('-created_at')
    
    # Filter for regular employees
    if request.user.role == 'employee':
        reviews = reviews.filter(employee__user=request.user)
        
    employee_id = request.GET.get('employee')
    selected_employee = None
    if employee_id:
        reviews = reviews.filter(employee_id=employee_id)
        from apps.employees.models import Employee
        selected_employee = Employee.objects.filter(id=employee_id).first()
        
    if search_query:
        reviews = reviews.filter(
            Q(employee__user__first_name__icontains=search_query) |
            Q(employee__user__last_name__icontains=search_query) |
            Q(period__icontains=search_query)
        )
        
    return render(request, 'performance.html', {
        'reviews': reviews, 
        'search_query': search_query,
        'selected_employee': selected_employee
    })
