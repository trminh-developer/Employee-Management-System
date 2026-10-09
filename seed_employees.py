import os
import sys
import django
import random
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import User
from apps.employees.models import Employee
from apps.departments.models import Department, Position
from django.contrib.auth.hashers import make_password

# Sample Vietnamese names
first_names_male = ['Hùng', 'Tuấn', 'Minh', 'Khoa', 'Hoàng', 'Duy', 'Phong', 'Thành', 'Nam', 'Hiếu', 'Bình', 'An', 'Phúc']
first_names_female = ['Hoa', 'Lan', 'Mai', 'Ngọc', 'Linh', 'Thảo', 'Trang', 'Hương', 'Nhung', 'Yến', 'Anh', 'Chi', 'Phương']
last_names = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ', 'Võ', 'Đặng', 'Bùi', 'Đỗ', 'Hồ', 'Ngô', 'Dương']
middle_names_male = ['Văn', 'Đức', 'Hữu', 'Công', 'Quang', 'Minh', 'Đình', 'Xuân', 'Gia']
middle_names_female = ['Thị', 'Bích', 'Thu', 'Thanh', 'Như', 'Tuyết', 'Hồng', 'Kim']

def generate_name(gender):
    last = random.choice(last_names)
    if gender == 'Male':
        mid = random.choice(middle_names_male)
        first = random.choice(first_names_male)
    else:
        mid = random.choice(middle_names_female)
        first = random.choice(first_names_female)
    return last, mid, first

def create_dummy_data():
    departments = list(Department.objects.all())
    if not departments:
        print("Không có phòng ban nào! Hãy tạo phòng ban trước.")
        return

    # Delete existing non-admin employees first? No, just add new ones
    start_id = Employee.objects.count() + 1
    
    positions_by_dept = {}
    
    # Create some default positions for each department if they don't exist
    # Create some default positions globally if they don't exist
    pos_titles = ['Nhân viên', 'Chuyên viên', 'Trưởng nhóm', 'Trưởng phòng', 'Phó giám đốc']
    positions = []
    for pt in pos_titles:
        p, _ = Position.objects.get_or_create(title=pt)
        positions.append(p)
        
    for dept in departments:
        positions_by_dept[dept.id] = positions

    count = 0
    # Generate 5-10 employees per department
    for dept in departments:
        num_employees = random.randint(5, 12)
        for _ in range(num_employees):
            gender = random.choice(['Male', 'Female'])
            last, mid, first = generate_name(gender)
            
            # Username generation
            import unidecode
            username_base = unidecode.unidecode(f"{first}{last}").lower().replace(' ', '')
            username = f"{username_base}{random.randint(1000, 99999)}"
            email = f"{username}@company.com"
            
            user = User.objects.create(
                username=username,
                email=email,
                first_name=f"{last} {mid}",
                last_name=first,
                role='employee',
                password=make_password('password123')
            )
            
            pos = random.choice(positions_by_dept[dept.id])
            
            # Random date of birth (22-45 years old)
            days_old = random.randint(22*365, 45*365)
            dob = date.today() - timedelta(days=days_old)
            
            # Random join date (last 3 years)
            days_join = random.randint(30, 3*365)
            join_date = date.today() - timedelta(days=days_join)
            
            phone = f"09{random.randint(10000000, 99999999)}"
            
            Employee.objects.create(
                user=user,
                employee_id=f"EMP{start_id:04d}",
                department=dept,
                position=pos,
                gender=gender,
                dob=dob,
                join_date=join_date,
                phone=phone,
                address=f"{random.randint(1, 999)} Nguyễn Trãi, Thanh Xuân, Hà Nội",
                status='active'
            )
            start_id += 1
            count += 1
            
    print(f"Đã tạo thành công {count} nhân viên mẫu cho các phòng ban!")

if __name__ == '__main__':
    create_dummy_data()
