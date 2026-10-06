from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def leave_list(request):
    return render(request, 'leave.html')
