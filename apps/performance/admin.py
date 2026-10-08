from django.contrib import admin
from .models import PerformanceReview

@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = ('employee', 'reviewer', 'period', 'score', 'created_at')
    search_fields = ('employee__user__first_name', 'employee__user__last_name', 'period')
    list_filter = ('period',)
