from django.db import models
from django.utils import timezone
from django.conf import settings
from django.db.models import Sum
from decimal import Decimal


class Payment(models.Model):
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments'
    )
    month = models.DateField(help_text="First day of the month this payment is for")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_date = models.DateField(default=timezone.now)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='collected_payments'
    )
    notes = models.TextField(blank=True)
    receipt = models.FileField(upload_to='payment_receipts/', blank=True, null=True)

    class Meta:
        ordering = ['-month', '-paid_date']

    def __str__(self):
        return f"{self.member} - {self.month.strftime('%B %Y')} - {self.amount}"

    @staticmethod
    def total_for_member_month(member, month):
        result = Payment.objects.filter(member=member, month=month).aggregate(t=Sum('amount'))
        return result['t'] or 0

    @staticmethod
    def status_for_member_month(member, month):
        total = Payment.total_for_member_month(member, month)
        minimum = member.effective_monthly_dues
        if total == 0:
            return 'unpaid', total, minimum
        elif total < minimum:
            return 'partial', total, minimum
        else:
            return 'paid', total, minimum


class Expense(models.Model):
    class Category(models.TextChoices):
        MAINTENANCE = 'maintenance', 'Maintenance'
        UTILITIES = 'utilities', 'Utilities'
        EVENT = 'event', 'Event'
        SUPPLIES = 'supplies', 'Supplies'
        OTHER = 'other', 'Other'

    description = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='expenses'
    )
    receipt = models.ImageField(upload_to='receipts/', blank=True, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.description} - {self.amount}"
