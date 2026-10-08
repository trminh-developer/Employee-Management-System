from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Department

@login_required
def departments_list(request):
    departments = Department.objects.select_related('manager').all()
    return render(request, 'departments.html', {'departments': departments})
