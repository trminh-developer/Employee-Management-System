from typing import Any
from django.db import models
from django.core.exceptions import ValidationError
from apps.employees.models import Employee


class LeaveRequest(models.Model):
    id: int
    pk: Any
    TYPE_CHOICES = [
        ('annual', 'Annual Leave'),
        ('sick', 'Sick Leave'),
        ('personal', 'Personal Leave'),
        ('unpaid', 'Unpaid Leave')
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending Manager'),
        ('approved_manager', 'Manager Approved'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    duration_days = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    attachment = models.FileField(upload_to='leave_docs/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError({
                    'end_date': 'Ngày kết thúc nghỉ phép không được nhỏ hơn ngày bắt đầu.'
                })

    def save(self, *args, **kwargs):
        self.clean()
        if self.start_date and self.end_date:
            self.duration_days = (self.end_date - self.start_date).days + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Leave {self.employee.user.username} - {self.start_date}"

