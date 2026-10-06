from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def departments_list(request):
    return render(request, 'departments.html')
