import os
import sys

# Ensure project root is on Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.departments.models import Department
from apps.employees.models import Employee

dept_prefix_map = {
    'Kỹ thuật': 'KT',
    'Finance & Accounting': 'FIN',
    'Administration': 'ADM',
    'HR': 'HR',
    'Sales': 'SAL',
    'Pháp chế': 'LEG',
    'Marketing': 'MKT',
    'R&D': 'RND',
}

position_rank = {
    'Giám đốc': 1,
    'Phó giám đốc': 2,
    'Trưởng phòng': 3,
    'Trưởng phòng kỹ thuật': 3,
    'Trưởng phòng CNTT': 3,
    'Trưởng phòng kỹ thuật và IT': 3,
    'Phó Trưởng phòng': 4,
    'Phó Trưởng phòng kỹ thuật': 4,
    'Phó Trưởng phòng CNTT': 4,
    'Phó Trưởng phòng kỹ thuật và IT': 4,
    'Tổ trưởng': 5,
    'Tổ trưởng kỹ thuật': 5,
    'Tổ trưởng CNTT': 5,
    'Tổ phó': 6,
    'Trưởng nhóm': 7,
    'Chuyên viên': 8,
    'Nhân viên': 9,
}

# Pass 1: Set temporary IDs to avoid unique constraint collisions
all_employees = list(Employee.objects.all())
print(f'Starting employee ID renumbering for {len(all_employees)} employees...')

for emp in all_employees:
    emp.employee_id = f'TMP_{emp.id:06d}'
    emp.save(update_fields=['employee_id'])

# Handle executive leadership (No department)
exec_leaders = Employee.objects.filter(department__isnull=True).order_by('id')
for seq, emp in enumerate(exec_leaders, start=1):
    emp.employee_id = f'{seq:04d}'
    emp.save(update_fields=['employee_id'])
    print(f'Executive Board: {emp.employee_id} - {emp.user.get_full_name()} ({emp.position.title if emp.position else "Lãnh đạo"})')

# Pass 2: Renumber per department
departments = Department.objects.all().order_by('id')
total_updated = 0

for d in departments:
    prefix = dept_prefix_map.get(d.name, 'EMP')
    emps = list(Employee.objects.filter(department=d).select_related('position', 'user'))

    def sort_key(e):
        rank = 99
        if e.position and e.position.title in position_rank:
            rank = position_rank[e.position.title]
        # Department manager is always head (rank 0)
        if d.manager and e.user_id == d.manager_id:
            rank = 0
        return (rank, e.id)

    emps.sort(key=sort_key)

    for seq, emp in enumerate(emps, start=1):
        emp.employee_id = f'{prefix}{seq:04d}'
        emp.save(update_fields=['employee_id'])
        total_updated += 1

    head = emps[0]
    tail = emps[-1]
    print(f'[{d.name}] Head: {head.employee_id} - {head.user.get_full_name()} ({head.position.title if head.position else "N/A"}) -> Range: {head.employee_id} to {tail.employee_id} ({len(emps)} members)')

print(f'\n[SUCCESS] Successfully renumbered {total_updated} department employees + {exec_leaders.count()} executives!')
