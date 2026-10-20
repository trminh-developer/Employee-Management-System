from typing import Any
from django.db import models
from django.conf import settings
from apps.departments.models import Department, Position

from django.core.validators import RegexValidator

class Employee(models.Model):
    id: int
    pk: Any
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('remote', 'Remote'),
        ('inactive', 'Inactive')
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_profile')
    
    employee_id_validator = RegexValidator(
        regex=r'^([A-Z]+\d{4}|\d{4})$',
        message="Mã nhân viên phải là Chữ in hoa + 4 số (VD: MKT0001), hoặc chỉ 4 số (VD: 0001) đối với Chủ tịch/Phó chủ tịch."
    )
    employee_id = models.CharField(max_length=20, unique=True, validators=[employee_id_validator], help_text="Định dạng: Chữ in hoa + 4 số, hoặc 4 số (với Ban Lãnh Đạo)")
    
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Personal Info
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], default='O')
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    join_date = models.DateField()
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        import re
        super().clean()
        
        # --- RULE 1: Chairman/Vice Chairman ID Format ---
        if self.employee_id:
            is_pure_number = bool(re.match(r'^\d{4}$', self.employee_id))
            title = self.position.title.strip().lower() if self.position else ''
            is_chairman = 'chủ tịch' in title
            
            if is_pure_number and not is_chairman:
                raise ValidationError({'employee_id': "Chỉ có Chủ tịch hoặc Phó chủ tịch mới được phép dùng mã nhân viên chỉ gồm 4 chữ số (VD: 0001)."})
            elif is_chairman and not is_pure_number:
                raise ValidationError({'employee_id': "Mã nhân viên của Chủ tịch/Phó chủ tịch phải là 4 chữ số (VD: 0001), không bao gồm chữ cái phòng ban."})
        
        # --- RULE 2: Department Position Limits ---
        if self.department and self.position and self.status in ['active', 'remote']:
            title = self.position.title.strip().lower()
            limited_titles = ['giám đốc', 'phó giám đốc', 'thư ký']
            
            if title in limited_titles:
                existing = Employee.objects.filter(
                    department=self.department,
                    position__title__iexact=self.position.title,
                    status__in=['active', 'remote']
                ).exclude(pk=self.pk)
                
                if existing.exists():
                    raise ValidationError({
                        'position': f"Phòng ban '{self.department.name}' đã có người đảm nhiệm chức vụ '{self.position.title}'. Mỗi phòng ban chỉ được phép có tối đa 1 Giám đốc, 1 Phó giám đốc và 1 Thư ký."
                    })

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.user_id:
            from django.contrib.auth import get_user_model
            UserModel = get_user_model()
            should_be_active = (self.status != 'inactive')
            UserModel.objects.filter(pk=self.user_id).exclude(is_active=should_be_active).update(is_active=should_be_active)
            if self.user and self.user.is_active != should_be_active:
                self.user.is_active = should_be_active

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"

