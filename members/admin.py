from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Member


@admin.register(Member)
class MemberAdmin(UserAdmin):
    list_display = ['username', 'first_name', 'last_name', 'role', 'phone', 'is_active_member', 'join_date', 'service_years']
    list_filter = ['role', 'is_active_member']
    search_fields = ['first_name', 'last_name', 'username', 'phone']
    fieldsets = UserAdmin.fieldsets + (
        ('Member Info', {'fields': ('role', 'phone', 'join_date', 'monthly_dues', 'is_active_member', 'avatar')}),
    )
