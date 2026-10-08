from django.db import models
from apps.employees.models import Employee

class Payroll(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('paid', 'Paid')
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payrolls')
    month = models.IntegerField()
    year = models.IntegerField()
    
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overtime_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    insurance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.gross_salary = (self.base_salary or 0) + (self.allowances or 0) + (self.overtime_pay or 0) + (self.bonus or 0)
        self.net_salary = self.gross_salary - (self.tax or 0) - (self.insurance or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payroll {self.month}/{self.year} - {self.employee.user.username}"
