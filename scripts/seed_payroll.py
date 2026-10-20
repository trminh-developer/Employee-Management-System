import os
import sys
import django
import random
import decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.employees.models import Employee
from apps.payroll.models import Payroll

def seed_payroll():
    employees = Employee.objects.all()
    if not employees.exists():
        print("Không có nhân viên nào trong hệ thống!")
        return

    count = 0
    # Xóa dữ liệu cũ nếu có
    Payroll.objects.filter(month=9, year=2026).delete()

    for emp in employees:
        # Lương cơ bản dựa theo vị trí
        base_salary = 10000000 # 10 triệu
        if emp.position:
            if 'Trưởng phòng' in emp.position.title or 'Phó giám đốc' in emp.position.title:
                base_salary = random.randint(25000000, 40000000)
            elif 'Trưởng nhóm' in emp.position.title:
                base_salary = random.randint(18000000, 24000000)
            elif 'Chuyên viên' in emp.position.title:
                base_salary = random.randint(12000000, 17000000)
            else:
                base_salary = random.randint(8000000, 11000000)

        allowances = random.randint(500000, 2000000)
        bonus = random.choice([0, 0, 1000000, 2000000, 5000000])
        
        # Tính thuế & BH
        tax = decimal.Decimal(base_salary) * decimal.Decimal('0.05')  # 5%
        insurance = decimal.Decimal(base_salary) * decimal.Decimal('0.08') # 8%

        Payroll.objects.create(
            employee=emp,
            month=9,
            year=2026,
            base_salary=base_salary,
            allowances=allowances,
            bonus=bonus,
            tax=tax,
            insurance=insurance,
            status='paid' # Set paid để hiện lên biểu đồ
        )
        count += 1

    print(f"Đã tạo thành công {count} bản ghi lương (Payroll) cho tháng 09/2026!")

if __name__ == '__main__':
    seed_payroll()
