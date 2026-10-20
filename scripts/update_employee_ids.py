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
    'Hội Đồng Quản Trị': 'BOD',
    'Ban Tổng Giám Đốc': 'BGD',
    'Ban Giám Đốc': 'BGD',
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
    'Chủ Tịch': 0,
    'Phó chủ tịch': 1,
    'Tổng Giám Đốc': 1,
    'Phó Tổng Giám Đốc': 2,
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
    'Thư ký Chủ tịch': 8,
    'Thư ký Tổng Giám Đốc': 8,
    'Thư ký': 8,
    'Chuyên viên': 9,
    'Nhân viên': 10,
}

def renumber_all():
    # Pass 1: Set temporary IDs to avoid unique constraint collisions
    all_employees = list(Employee.objects.all())
    print(f'Starting employee ID verification & renumbering for {len(all_employees)} employees...')

    for emp in all_employees:
        emp.employee_id = f'TMP_{emp.id:06d}'
        emp.save(update_fields=['employee_id'])

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

        # Special handling for Hội Đồng Quản Trị:
        # Only Chủ tịch (0001) and Phó chủ tịch (0002) get 4 pure digits!
        # Others in BOD (e.g. Thư ký Chủ tịch) get BOD0001, BOD0002...
        if prefix == 'BOD':
            bod_seq = 1
            for emp in emps:
                title = emp.position.title.strip().lower() if emp.position else ''
                if title == 'chủ tịch':
                    emp.employee_id = '0001'
                elif title == 'phó chủ tịch':
                    emp.employee_id = '0002'
                else:
                    emp.employee_id = f'BOD{bod_seq:04d}'
                    bod_seq += 1
                emp.save(update_fields=['employee_id'])
                total_updated += 1
        else:
            for seq, emp in enumerate(emps, start=1):
                emp.employee_id = f'{prefix}{seq:04d}'
                emp.save(update_fields=['employee_id'])
                total_updated += 1

        head = emps[0]
        tail = emps[-1]
        print(f'[{d.name}] Head: {head.employee_id} - {head.user.get_full_name()} ({head.position.title if head.position else "N/A"}) -> Range: {head.employee_id} to {tail.employee_id} ({len(emps)} members)')

    # Handle any employee outside departments
    unassigned = Employee.objects.filter(department__isnull=True).order_by('id')
    for seq, emp in enumerate(unassigned, start=1):
        emp.employee_id = f'EMP{seq:04d}'
        emp.save(update_fields=['employee_id'])
        print(f'[Unassigned] {emp.employee_id} - {emp.user.get_full_name()}')

    print(f'\n[SUCCESS] Successfully verified and renumbered {total_updated} employees across all departments!')

if __name__ == '__main__':
    renumber_all()
