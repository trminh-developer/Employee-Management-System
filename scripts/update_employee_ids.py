import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.employees.models import Employee
import re

prefix_map = {
    'Kỹ thuật': 'KT',
    'Finance & Accounting': 'FIN',
    'Administration': 'ADM',
    'HR': 'HR',
    'Sales': 'SAL',
    'Pháp chế': 'LEG',
    'Marketing': 'MKT',
    'R&D': 'RND',
}

employees = list(Employee.objects.select_related('department').all())
updated = 0
for emp in employees:
    dept_name = emp.department.name if emp.department else ''
    prefix = prefix_map.get(dept_name, 'EMP')
        
    nums = re.findall(r'\d+', emp.employee_id)
    if nums:
        number_str = nums[-1].zfill(4)
    else:
        number_str = f'{emp.id:04d}'
        
    if len(number_str) > 4:
        number_str = number_str[-4:]
        
    new_id = f'{prefix}{number_str}'
    
    if emp.employee_id != new_id:
        # Avoid collision
        if Employee.objects.filter(employee_id=new_id).exclude(id=emp.id).exists():
            new_id = f'{prefix}{emp.id:04d}'
            
        emp.employee_id = new_id
        emp.save()
        updated += 1

print(f'Successfully updated {updated} employee IDs')
