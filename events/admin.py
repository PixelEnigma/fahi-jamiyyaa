from django.contrib import admin
from .models import Event, EventPhoto


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'location', 'status', 'organizer']
    list_filter = ['status', 'date']
    search_fields = ['title', 'location']


@admin.register(EventPhoto)
class EventPhotoAdmin(admin.ModelAdmin):
    list_display = ['event', 'caption', 'uploaded_at']
