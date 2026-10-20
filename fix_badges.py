import os
import re

def process_file(filepath, app_model):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Fix Badges
    # Find spans like: <span style="padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: 600; \n {% if ... %\}background:#c6f6d5;color:#22543d; ...">
    # Replace with: <span class="badge {% if ... %\}badge-success{% elif ... %\}badge-warning{% else %\}badge-danger{% endif %\}">
    
    # Regex for attendance
    content = re.sub(
        r'<span style="padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;\s*\{% if rec\.status == \'present\' %\}background:#c6f6d5;color:#22543d;\s*\{% elif rec\.status == \'late\' %\}background:#feebc8;color:#7b341e;\s*\{% else %\}background:#fed7d7;color:#9b2c2c;\{% endif %\}">',
        r'<span class="badge {% if rec.status == \'present\' %}badge-success{% elif rec.status == \'late\' %}badge-warning{% else %}badge-danger{% endif %}">',
        content
    )
    # Regex for leave
    content = re.sub(
        r'<span style="padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;\s*\{% if req\.status == \'approved\' %\}background:#c6f6d5;color:#22543d;\s*\{% elif req\.status == \'rejected\' %\}background:#fed7d7;color:#9b2c2c;\s*\{% else %\}background:#e2e8f0;color:#4a5568;\{% endif %\}">',
        r'<span class="badge {% if req.status == \'approved\' %}badge-success{% elif req.status == \'rejected\' %}badge-danger{% else %}badge-secondary{% endif %}">',
        content
    )
    # Regex for payroll
    content = re.sub(
        r'<span style="padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;\s*\{% if rec\.status == \'paid\' %\}background:#c6f6d5;color:#22543d;\s*\{% elif rec\.status == \'approved\' %\}background:#bee3f8;color:#2c5282;\s*\{% else %\}background:#e2e8f0;color:#4a5568;\{% endif %\}">',
        r'<span class="badge {% if rec.status == \'paid\' %}badge-success{% elif rec.status == \'approved\' %}badge-primary{% else %}badge-secondary{% endif %}">',
        content
    )
    # Regex for notifications
    content = re.sub(
        r'<span style="padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;\s*\{% if n\.priority == \'critical\' %\}background:#fed7d7;color:#9b2c2c;\s*\{% elif n\.priority == \'high\' %\}background:#feebc8;color:#7b341e;\s*\{% else %\}background:#e2e8f0;color:#4a5568;\{% endif %\}">',
        r'<span class="badge {% if n.priority == \'critical\' %}badge-danger{% elif n.priority == \'high\' %}badge-warning{% else %}badge-secondary{% endif %}">',
        content
    )
    
    # 2. Update Table Headers to include "Thao tác" if missing
    # Search for the last </th> before </tr></thead> and ensure "Thao tác" is there.
    # We will do this manually for files that need it.

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


files = [
    ('templates/attendance.html', 'attendance/attendance'),
    ('templates/leave.html', 'leave/leaverequest'),
    ('templates/performance.html', 'performance/performancereview'),
    ('templates/notifications.html', 'notifications/notification'),
    ('templates/payroll.html', 'payroll/payroll'),
    ('templates/accounts/user_list.html', 'accounts/user')
]

for filepath, model in files:
    process_file(filepath, model)
    print(f"Processed {filepath}")
