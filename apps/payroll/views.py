from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def payroll_list(request):
    return render(request, 'payroll.html')
