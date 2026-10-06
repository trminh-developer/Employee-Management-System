from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def notifications_list(request):
    return render(request, 'notifications.html')
