from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def performance_list(request):
    return render(request, 'performance.html')
