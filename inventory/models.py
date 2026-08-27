from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.conf import settings


class InventoryItem(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        LEASED = 'leased', 'Leased'
        MAINTENANCE = 'maintenance', 'Under Maintenance'
        DAMAGED = 'damaged', 'Damaged'

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    available_quantity = models.IntegerField(default=1, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    purchase_date = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='inventory/', blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'inventory items'

    def __str__(self):
        return f"{self.name} ({self.available_quantity}/{self.quantity})"


class Lease(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='leases')
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leases'
    )
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    lease_date = models.DateTimeField(default=timezone.now)
    expected_return_date = models.DateTimeField()
    returned_date = models.DateTimeField(null=True, blank=True)
    purpose = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-lease_date']

    def __str__(self):
        return f"{self.item} -> {self.member} ({self.lease_date.strftime('%d %b %Y')})"

    @property
    def is_overdue(self):
        if self.returned_date:
            return False
        return timezone.now() > self.expected_return_date
