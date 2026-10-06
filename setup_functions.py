import os

BASE_DIR = r"e:\Project\HeThongQuanLyNhanVien"
APPS_DIR = os.path.join(BASE_DIR, "apps")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

apps = [
    ("employees", "employees.html"),
    ("departments", "departments.html"),
    ("attendance", "attendance.html"),
    ("leave", "leave.html"),
    ("payroll", "payroll.html"),
    ("performance", "performance.html"),
    ("reports", "reports.html"),
    ("notifications", "notifications.html"),
]

def setup_all_functions():
    for app_name, template_name in apps:
        app_path = os.path.join(APPS_DIR, app_name)
        
        # 1. Create Views
        views_content = f"""from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def {app_name}_list(request):
    return render(request, '{template_name}')
"""
        with open(os.path.join(app_path, "views.py"), "w", encoding="utf-8") as f:
            f.write(views_content)
            
        # 2. Create URLs
        urls_content = f"""from django.urls import path
from . import views

app_name = '{app_name}'

urlpatterns = [
    path('', views.{app_name}_list, name='list'),
]
"""
        with open(os.path.join(app_path, "urls.py"), "w", encoding="utf-8") as f:
            f.write(urls_content)
            
        # 3. Create Template if it doesn't exist
        template_path = os.path.join(TEMPLATES_DIR, template_name)
        if not os.path.exists(template_path):
            title = app_name.capitalize()
            dummy_html = f"""{{% extends 'base.html' %}}
{{% block title %}}{title} - Employee Management{{% endblock %}}

{{% block content %}}
<div class="page-header">
    <h1>{title}</h1>
    <p style="color: var(--text-secondary); margin-top: 0.5rem;">Manage {title} operations.</p>
</div>
<div style="padding: 2rem; background: var(--bg-surface); border-radius: var(--radius-lg); border: 1px solid var(--border-color); text-align: center; color: var(--text-secondary);">
    <i data-lucide="layout-grid" style="width: 48px; height: 48px; margin-bottom: 1rem; opacity: 0.5;"></i>
    <h2>Module In Development</h2>
    <p>This module is part of the architectural scaffolding and will be expanded shortly.</p>
</div>
{{% endblock %}}
"""
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(dummy_html)

if __name__ == "__main__":
    setup_all_functions()
    print("Successfully scaffolded views, urls, and templates for all apps.")
