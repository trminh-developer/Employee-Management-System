from django.contrib import admin

from django.http import HttpResponseRedirect

class FrontendRedirectMixin:
    def response_change(self, request, obj):
        res = super().response_change(request, obj)
        if 'next' in request.GET and getattr(res, 'status_code', 200) in [301, 302]:
            return HttpResponseRedirect(request.GET['next'])
        return res
        
    def response_add(self, request, obj, addition=True):
        res = super().response_add(request, obj, addition)
        if 'next' in request.GET and getattr(res, 'status_code', 200) in [301, 302]:
            return HttpResponseRedirect(request.GET['next'])
        return res

from .models import Notification

@admin.register(Notification)
class NotificationAdmin(FrontendRedirectMixin, admin.ModelAdmin):
    list_display = ('user', 'title', 'is_read', 'created_at')
