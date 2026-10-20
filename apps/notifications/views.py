from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from .models import Notification


@login_required
def notifications_list(request):
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at', '-id')
    return render(request, 'notifications.html', {'notifs': notifs})


@login_required
def mark_all_read(request):
    if request.method != 'POST':
        return JsonResponse({'detail': 'Method not allowed'}, status=405)

    with transaction.atomic():
        updated_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)

    wants_json = (
        'application/json' in request.headers.get('Accept', '')
        or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    )
    if wants_json:
        return JsonResponse({
            'status': 'completed',
            'updated_count': updated_count
        }, status=200)

    return redirect('notifications:list')

