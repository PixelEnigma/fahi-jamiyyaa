from django.contrib import admin
from .models import Sponsor, Contribution


@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    list_display = ['name', 'tier', 'total_contribution', 'is_active']
    list_filter = ['tier', 'is_active']
    search_fields = ['name', 'contact_person']


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ['sponsor', 'amount', 'date', 'event']
    list_filter = ['date']
    search_fields = ['sponsor__name']
