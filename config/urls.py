from django.contrib import admin
from django.urls import path, include, reverse
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from apps.employees.views import dashboard


def robots_txt(request):
    sitemap_url = request.build_absolute_uri('/sitemap.xml')
    lines = [
        "User-agent: *",
        "Allow: /accounts/login/",
        "Allow: /static/",
        "Disallow: /admin/",
        "Disallow: /api/",
        "Disallow: /employees/",
        "Disallow: /departments/",
        "Disallow: /attendance/",
        "Disallow: /leave/",
        "Disallow: /payroll/",
        "Disallow: /performance/",
        "Disallow: /reports/",
        "Disallow: /notifications/",
        "Disallow: /accounts/users/",
        "Disallow: /*?_popup=",
        f"Sitemap: {sitemap_url}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


def sitemap_xml(request):
    login_url = request.build_absolute_uri(reverse('accounts:login'))
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{login_url}</loc>
        <changefreq>monthly</changefreq>
        <priority>1.0</priority>
    </url>
</urlset>"""
    return HttpResponse(xml_content, content_type="application/xml; charset=utf-8")


urlpatterns = [
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap_xml, name='sitemap_xml'),
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

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

