from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('hr', 'HR Manager'),
        ('manager', 'Manager'),
        ('employee', 'Employee'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    
    def save(self, *args, **kwargs):
        if self.role in ['admin', 'hr', 'manager']:
            self.is_staff = True
        if self.role == 'admin':
            self.is_superuser = True
        super().save(*args, **kwargs)

    def has_perm(self, perm, obj=None):
        if self.is_superuser or self.role == 'admin':
            return True
        if self.role == 'hr':
            # HR can do anything with employees, departments, leave, attendance, payroll
            app_label = perm.split('.')[0]
            if app_label in ['employees', 'departments', 'leave', 'attendance', 'payroll', 'accounts']:
                return True
        if self.role == 'manager':
            # Manager can view stuff and approve leave
            if 'view' in perm or 'change_leaverequest' in perm:
                return True
        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        if self.is_superuser or self.role == 'admin':
            return True
        if self.role in ['hr', 'manager']:
            return True
        return super().has_module_perms(app_label)

    def get_full_name(self):
        """Họ trước, Tên sau (Vietnamese format)"""
        full_name = f"{self.last_name} {self.first_name}".strip()
        return full_name or self.username

    def __str__(self):
        return self.username
