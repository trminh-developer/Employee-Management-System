import os
import subprocess
import shutil

def run_cmd(cmd, cwd=None):
    subprocess.run(cmd, shell=True, check=True, cwd=cwd)

def setup_django_modular():
    base_dir = os.getcwd()
    
    # 1. Initialize project named 'config'
    run_cmd("python -m django startproject config .")
    
    # 2. Create directory structure
    dirs = [
        "apps",
        "templates",
        "templates/shared",
        "static/css",
        "static/js",
        "static/images",
        "media"
    ]
    for d in dirs:
        os.makedirs(os.path.join(base_dir, d), exist_ok=True)
        
    # Make apps a Python package
    with open(os.path.join(base_dir, "apps", "__init__.py"), "w") as f:
        f.write("")

    # 3. Create all apps inside the apps/ directory
    app_names = [
        "accounts",
        "employees",
        "departments",
        "attendance",
        "leave",
        "payroll",
        "performance",
        "reports",
        "notifications"
    ]
    
    for app in app_names:
        app_path = os.path.join(base_dir, "apps", app)
        os.makedirs(app_path, exist_ok=True)
        # Create app using django-admin
        run_cmd(f"python manage.py startapp {app} {app_path}")
        
        # Update apps.py to reflect the correct name ('apps.appname')
        apps_py_path = os.path.join(app_path, "apps.py")
        with open(apps_py_path, "r") as f:
            content = f.read()
        content = content.replace(f"name = '{app}'", f"name = 'apps.{app}'")
        with open(apps_py_path, "w") as f:
            f.write(content)
            
        # Create urls.py for each app
        with open(os.path.join(app_path, "urls.py"), "w") as f:
            f.write("from django.urls import path\nfrom . import views\n\napp_name = '" + app + "'\n\nurlpatterns = [\n]\n")

    print("Scaffolding completed successfully.")

if __name__ == "__main__":
    setup_django_modular()
