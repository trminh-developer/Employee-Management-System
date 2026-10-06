from django.db import models
from apps.employees.models import Employee

class PerformanceReview(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='given_reviews')
    period = models.CharField(max_length=50) # e.g. 'Q3 2024'
    score = models.DecimalField(max_digits=5, decimal_places=2)
    feedback = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
