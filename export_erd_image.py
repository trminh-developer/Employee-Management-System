import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import shutil

# Set up figure
fig, ax = plt.subplots(figsize=(26, 16), dpi=200)
fig.patch.set_facecolor('#0f172a')
ax.set_facecolor('#0f172a')

# Table schemas: (name, table_db_name, [(name, type, is_pk, is_fk)])
tables = {
    'User': {
        'pos': (1, 10.5), 'size': (4.2, 4.2), 'color': '#3b82f6',
        'table': 'accounts_user',
        'fields': [
            ('id', 'BIGINT', True, False),
            ('username', 'VARCHAR(150)', False, False),
            ('email', 'VARCHAR(254)', False, False),
            ('password', 'VARCHAR(128)', False, False),
            ('first_name', 'VARCHAR(150)', False, False),
            ('last_name', 'VARCHAR(150)', False, False),
            ('role', 'VARCHAR(20)', False, False),
            ('is_superuser', 'BOOLEAN', False, False),
            ('is_staff', 'BOOLEAN', False, False),
            ('is_active', 'BOOLEAN', False, False),
            ('date_joined', 'DATETIME', False, False),
        ]
    },
    'Employee': {
        'pos': (7.5, 9.0), 'size': (4.8, 5.8), 'color': '#6366f1',
        'table': 'employees_employee',
        'fields': [
            ('id', 'BIGINT', True, False),
            ('user_id', 'BIGINT', False, True),
            ('employee_id', 'VARCHAR(20)', False, False),
            ('department_id', 'BIGINT', False, True),
            ('position_id', 'BIGINT', False, True),
            ('manager_id', 'BIGINT', False, True),
            ('dob', 'DATE', False, False),
            ('gender', 'VARCHAR(10)', False, False),
            ('phone', 'VARCHAR(15)', False, False),
            ('address', 'TEXT', False, False),
            ('status', 'VARCHAR(20)', False, False),
            ('join_date', 'DATE', False, False),
            ('avatar', 'VARCHAR(100)', False, False),
            ('created_at', 'DATETIME', False, False),
        ]
    },
    'Department': {
        'pos': (14.5, 11.0), 'size': (4.4, 3.8), 'color': '#0ea5e9',
        'table': 'departments_department',
        'fields': [
            ('id', 'BIGINT', True, False),
            ('name', 'VARCHAR(100)', False, False),
            ('description', 'TEXT', False, False),
            ('manager_id', 'BIGINT', False, True),
            ('parent_id', 'BIGINT', False, True),
            ('budget', 'DECIMAL(12,2)', False, False),
            ('created_at', 'DATETIME', False, False),
        ]
    },
    'Position': {
        'pos': (14.5, 6.5), 'size': (4.4, 2.8), 'color': '#14b8a6',
        'table': 'departments_position',
        'fields': [
            ('id', 'BIGINT', True, False),
            ('title', 'VARCHAR(100)', False, False),
            ('department_id', 'BIGINT', False, True),
        ]
    },
    'Attendance': {
        'pos': (1.0, 3.2), 'size': (4.4, 3.8), 'color': '#10b981',
        'table': 'attendance_attendance',
        'fields': [
            ('id', 'BIGINT', True, False),
            ('employee_id', 'BIGINT', False, True),
            ('date', 'DATE', False, False),
            ('check_in', 'TIME', False, False),
            ('check_out', 'TIME', False, False),
            ('status', 'VARCHAR(20)', False, False),
            ('overtime_hours', 'DECIMAL(4,2)', False, False),
            ('note', 'VARCHAR(255)', False, False),
        ]
    },
    'LeaveRequest': {
        'pos': (7.5, 2.8), 'size': (4.8, 4.4), 'color': '#f59e0b',
        'table': 'leave_leaverequest',
        'fields': [
            ('id', 'BIGINT', True, False),
            ('employee_id', 'BIGINT', False, True),
            ('leave_type', 'VARCHAR(20)', False, False),
            ('start_date', 'DATE', False, False),
            ('end_date', 'DATE', False, False),
            ('duration_days', 'DECIMAL(4,1)', False, False),
            ('status', 'VARCHAR(20)', False, False),
            ('reason', 'TEXT', False, False),
            ('attachment', 'VARCHAR(100)', False, False),
        ]
    },
    'Payroll': {
        'pos': (14.5, 0.8), 'size': (4.8, 5.0), 'color': '#ec4899',
        'table': 'payroll_payroll',
        'fields': [
            ('id', 'BIGINT', True, False),
            ('employee_id', 'BIGINT', False, True),
            ('month', 'INT', False, False),
            ('year', 'INT', False, False),
            ('base_salary', 'DECIMAL(12,2)', False, False),
            ('allowances', 'DECIMAL(12,2)', False, False),
            ('bonus', 'DECIMAL(12,2)', False, False),
            ('tax', 'DECIMAL(12,2)', False, False),
            ('insurance', 'DECIMAL(12,2)', False, False),
            ('net_salary', 'DECIMAL(12,2)', False, False),
            ('status', 'VARCHAR(20)', False, False),
        ]
    },
    'PerformanceReview': {
        'pos': (21.0, 9.0), 'size': (4.6, 3.8), 'color': '#8b5cf6',
        'table': 'performance_performancereview',
        'fields': [
            ('id', 'BIGINT', True, False),
            ('employee_id', 'BIGINT', False, True),
            ('reviewer_id', 'BIGINT', False, True),
            ('period', 'VARCHAR(20)', False, False),
            ('score', 'DECIMAL(3,1)', False, False),
            ('feedback', 'TEXT', False, False),
            ('created_at', 'DATETIME', False, False),
        ]
    },
    'Notification': {
        'pos': (21.0, 3.5), 'size': (4.6, 3.8), 'color': '#f43f5e',
        'table': 'notifications_notification',
        'fields': [
            ('id', 'BIGINT', True, False),
            ('user_id', 'BIGINT', False, True),
            ('title', 'VARCHAR(255)', False, False),
            ('message', 'TEXT', False, False),
            ('category', 'VARCHAR(50)', False, False),
            ('priority', 'VARCHAR(20)', False, False),
            ('is_read', 'BOOLEAN', False, False),
            ('created_at', 'DATETIME', False, False),
        ]
    }
}

# Draw tables
for tname, data in tables.items():
    x, y = data['pos']
    w, h = data['size']
    color = data['color']
    
    # Outer card with rounded corners
    box = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.08,rounding_size=0.18",
        facecolor='#1e293b', edgecolor='#334155', linewidth=1.5, zorder=2
    )
    ax.add_patch(box)
    
    # Header bar
    hh = 0.65
    header = patches.FancyBboxPatch(
        (x, y + h - hh), w, hh,
        boxstyle="round,pad=0.08,rounding_size=0.18",
        facecolor=color, edgecolor='none', zorder=3
    )
    ax.add_patch(header)
    
    # Rect to flatten bottom of header
    ax.fill_between([x, x+w], y + h - hh, y + h - hh*0.5, color=color, zorder=3)
    
    # Header title
    ax.text(x + 0.2, y + h - hh/2 + 0.08, tname, fontsize=12, fontweight='bold', color='#ffffff', zorder=4)
    ax.text(x + 0.2, y + h - hh/2 - 0.16, f"({data['table']})", fontsize=7.5, color='#cbd5e1', zorder=4)
    
    # Fields
    field_y = y + h - hh - 0.25
    line_step = (h - hh - 0.3) / max(len(data['fields']), 1)
    
    for fname, ftype, is_pk, is_fk in data['fields']:
        badge_x = x + 0.2
        if is_pk:
            badge = patches.Rectangle((badge_x, field_y - 0.02), 0.35, 0.18, facecolor='#eab308', edgecolor='none', zorder=4)
            ax.add_patch(badge)
            ax.text(badge_x + 0.175, field_y + 0.07, 'PK', fontsize=6, fontweight='bold', color='#000000', ha='center', va='center', zorder=5)
            fname_color = '#fef08a'
        elif is_fk:
            badge = patches.Rectangle((badge_x, field_y - 0.02), 0.35, 0.18, facecolor='#38bdf8', edgecolor='none', zorder=4)
            ax.add_patch(badge)
            ax.text(badge_x + 0.175, field_y + 0.07, 'FK', fontsize=6, fontweight='bold', color='#000000', ha='center', va='center', zorder=5)
            fname_color = '#bae6fd'
        else:
            fname_color = '#cbd5e1'
            
        ax.text(x + 0.65, field_y + 0.07, fname, fontsize=8, fontweight='500', color=fname_color, va='center', zorder=4)
        ax.text(x + w - 0.2, field_y + 0.07, ftype, fontsize=7.5, color='#64748b', ha='right', va='center', zorder=4)
        
        field_y -= line_step

# Draw relationships (connecting lines)
relationships = [
    # (From Table, To Table, start_pt, end_pt, label)
    ('Employee', 'User', (7.5, 14.0), (5.2, 14.0), 'user_id -> id (1:1)'),
    ('Employee', 'Department', (12.3, 13.0), (14.5, 13.0), 'department_id -> id (N:1)'),
    ('Employee', 'Position', (12.3, 10.5), (14.5, 8.0), 'position_id -> id (N:1)'),
    ('Position', 'Department', (16.7, 9.3), (16.7, 11.0), 'department_id -> id (N:1)'),
    ('Attendance', 'Employee', (5.4, 5.5), (7.5, 9.5), 'employee_id -> id (N:1)'),
    ('LeaveRequest', 'Employee', (9.9, 7.2), (9.9, 9.0), 'employee_id -> id (N:1)'),
    ('Payroll', 'Employee', (14.5, 4.0), (12.3, 9.5), 'employee_id -> id (N:1)'),
    ('PerformanceReview', 'Employee', (21.0, 11.0), (12.3, 11.5), 'employee_id -> id (N:1)'),
    ('Notification', 'User', (21.0, 5.0), (5.2, 11.5), 'user_id -> id (N:1)'),
]

for src, dst, p1, p2, lbl in relationships:
    verts = [
        p1,
        ((p1[0] + p2[0]) / 2, p1[1]),
        ((p1[0] + p2[0]) / 2, p2[1]),
        p2
    ]
    codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]
    path = Path(verts, codes)
    patch = patches.PathPatch(path, facecolor='none', edgecolor='#475569', linewidth=1.8, linestyle='--', zorder=1, alpha=0.85)
    ax.add_patch(patch)
    
    # Dot at destination
    ax.plot(p2[0], p2[1], marker='o', markersize=5, color='#38bdf8', zorder=5)

# Title & Watermark
ax.text(1.0, 15.3, "ENTERPRISE HR MANAGEMENT SYSTEM (EMS)", fontsize=18, fontweight='bold', color='#f8fafc', zorder=10)
ax.text(1.0, 14.9, "Entity Relationship Diagram (ERD) - Full Database Schema Architecture", fontsize=11, color='#94a3b8', zorder=10)

ax.set_xlim(0, 26.5)
ax.set_ylim(0, 16.0)
ax.axis('off')

plt.tight_layout()

# Save image
out_path = r'E:\Project\HeThongQuanLyNhanVien\database_erd.png'
plt.savefig(out_path, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
print(f"ERD Image exported successfully to {out_path}")

# Copy to artifacts directory
artifact_dir = r'C:\Users\TrMinh\.gemini\antigravity\brain\007ea8fc-0d8b-431d-a75a-5d94ae822349'
shutil.copy2(out_path, os.path.join(artifact_dir, 'database_erd.png'))
print(f"Copied to artifact dir: {artifact_dir}")
