from django.contrib import admin
from django.urls import path, include
from apps.employees.views import dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),
    path('employees/', include('apps.employees.urls')),
    path('departments/', include('apps.departments.urls')),
    path('attendance/', include('apps.attendance.urls')),
    path('leave/', include('apps.leave.urls')),
    path('payroll/', include('apps.payroll.urls')),
    path('performance/', include('apps.performance.urls')),
    path('reports/', include('apps.reports.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('accounts/', include('apps.accounts.urls')),
]
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
