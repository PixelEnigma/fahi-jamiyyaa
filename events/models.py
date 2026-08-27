from django.db import models
from django.utils import timezone
from django.conf import settings


class Event(models.Model):
    class Status(models.TextChoices):
        PLANNED = 'planned', 'Planned'
        ORGANIZED = 'organized', 'Organized'
        CANCELLED = 'cancelled', 'Cancelled'

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    date = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='organized_events'
    )
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    outcome_notes = models.TextField(blank=True, help_text="Notes about how the event went")
    cancellation_reason = models.TextField(blank=True, help_text="Reason for cancelling this event")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return self.title

    @property
    def is_past(self):
        return timezone.now() > self.date


class EventPhoto(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='event_photos/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f"Photo for {self.event.title} - {self.caption or 'No caption'}"
