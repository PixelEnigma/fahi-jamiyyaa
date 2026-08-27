from django.contrib import admin
from .models import Payment, Expense


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['member', 'month', 'amount', 'paid_date', 'received_by']
    list_filter = ['month', 'paid_date']
    search_fields = ['member__first_name', 'member__last_name', 'member__username']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['description', 'category', 'amount', 'date', 'paid_by']
    list_filter = ['category', 'date']
    search_fields = ['description']
