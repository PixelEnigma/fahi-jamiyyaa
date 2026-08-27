from django.contrib import admin
from .models import Notice


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ['title', 'priority', 'created_by', 'created_at', 'pinned']
    list_filter = ['priority', 'pinned']
    search_fields = ['title']
