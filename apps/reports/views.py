from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def reports_list(request):
    return render(request, 'reports.html')
