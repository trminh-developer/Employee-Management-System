from django.contrib import admin
from django import forms
from django.http import HttpResponseRedirect
from .models import Employee
from apps.accounts.models import User

class EmployeeAdminForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False, label='Tên')
    last_name = forms.CharField(max_length=150, required=False, label='Họ')
    email = forms.EmailField(required=False, label='Thư điện tử (Email)')
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=False, label='Vai trò (Role)')

    class Meta:
        model = Employee
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['role'].initial = self.instance.user.role

    def save(self, commit=True):
        employee = super().save(commit=False)
        if commit:
            employee.save()
            self.save_m2m()
            
        if employee.user:
            employee.user.first_name = self.cleaned_data.get('first_name', '')
            employee.user.last_name = self.cleaned_data.get('last_name', '')
            employee.user.email = self.cleaned_data.get('email', '')
            
            # Update role if provided
            role_val = self.cleaned_data.get('role')
            if role_val:
                employee.user.role = role_val
                
            employee.user.save()
        return employee

class FrontendRedirectMixin:
    def response_change(self, request, obj):
        res = super().response_change(request, obj)
        if 'next' in request.GET and getattr(res, 'status_code', 200) in [301, 302]:
            return HttpResponseRedirect(request.GET['next'])
        return res
        
    def response_add(self, request, obj, addition=True):
        res = super().response_add(request, obj, addition)
        if 'next' in request.GET and getattr(res, 'status_code', 200) in [301, 302]:
            return HttpResponseRedirect(request.GET['next'])
        return res

@admin.register(Employee)
class EmployeeAdmin(FrontendRedirectMixin, admin.ModelAdmin):
    form = EmployeeAdminForm
    list_display = ('employee_id', 'user', 'department', 'position', 'status')
    
    # Organize fields so that user info is grouped
    fieldsets = (
        ('Thông tin Tài khoản liên kết', {
            'fields': ('user', 'role', 'last_name', 'first_name', 'email')
        }),
        ('Thông tin Công việc', {
            'fields': ('employee_id', 'department', 'position', 'manager', 'status', 'join_date')
        }),
        ('Thông tin Cá nhân', {
            'fields': ('dob', 'gender', 'phone', 'address', 'avatar')
        }),
    )
