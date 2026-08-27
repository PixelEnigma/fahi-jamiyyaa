from django.contrib import admin
from .models import InventoryItem, Lease


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'quantity', 'available_quantity', 'status', 'purchase_date']
    list_filter = ['status']
    search_fields = ['name']


@admin.register(Lease)
class LeaseAdmin(admin.ModelAdmin):
    list_display = ['item', 'member', 'quantity', 'lease_date', 'expected_return_date', 'is_overdue']
    list_filter = ['lease_date']
    search_fields = ['item__name', 'member__first_name', 'member__last_name']
