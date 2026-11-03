from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from .models import Department

@login_required
def departments_list(request):
    search_query = request.GET.get('q', '').strip()
    departments = Department.objects.select_related('manager', 'manager__employee_profile', 'parent').annotate(
        employee_count=Count('employees')
    ).order_by('name')

    if search_query:
        departments = departments.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(manager__first_name__icontains=search_query) |
            Q(manager__last_name__icontains=search_query) |
            Q(manager__username__icontains=search_query) |
            Q(parent__name__icontains=search_query)
        )

    return render(request, 'departments.html', {
        'departments': departments,
        'search_query': search_query,
    })
